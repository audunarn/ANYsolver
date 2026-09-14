"""Arithmetic only for Q(sqrt(2), sqrt(3), sqrt(5)); no mechanics or I/O."""
from fractions import Fraction
from math import isqrt


class Field:
    __slots__ = ('c',)

    def __init__(self, value=0):
        if isinstance(value, Field):
            self.c = value.c
        elif isinstance(value, (int, Fraction, str)) and not isinstance(value, bool):
            self.c = (Fraction(value),) + (Fraction(0),) * 7
        else:
            raise TypeError('exact rational or Field required')

    @classmethod
    def from_coefficients(cls, values):
        values = tuple(values)
        if len(values) != 8 or any(not isinstance(x, (int, str, Fraction)) or isinstance(x, bool) for x in values):
            raise ValueError('eight exact rational coefficients required')
        result = object.__new__(cls)
        result.c = tuple(Fraction(x) for x in values)
        return result

    @classmethod
    def root(cls, prime):
        mask = {2: 1, 3: 2, 5: 4}[prime]
        values = [0] * 8
        values[mask] = 1
        return cls.from_coefficients(values)

    def coefficients(self):
        return [str(x) for x in self.c]

    def __bool__(self):
        return any(self.c)

    def __eq__(self, other):
        try:
            return self.c == Field(other).c
        except (TypeError, ValueError):
            return False

    def __neg__(self):
        return Field.from_coefficients(-x for x in self.c)

    def __add__(self, other):
        other = Field(other)
        return Field.from_coefficients(x + y for x, y in zip(self.c, other.c))

    __radd__ = __add__

    def __sub__(self, other):
        return self + (-Field(other))

    def __rsub__(self, other):
        return Field(other) - self

    def __mul__(self, other):
        other = Field(other)
        if not any(self.c[1:]):
            return Field.from_coefficients(self.c[0] * y for y in other.c)
        if not any(other.c[1:]):
            return Field.from_coefficients(other.c[0] * x for x in self.c)
        values = [Fraction(0)] * 8
        for i, x in enumerate(self.c):
            if x:
                for j, y in enumerate(other.c):
                    if y:
                        overlap = i & j
                        factor = (2 if overlap & 1 else 1) * (3 if overlap & 2 else 1) * (5 if overlap & 4 else 1)
                        values[i ^ j] += x * y * factor
        return Field.from_coefficients(values)

    __rmul__ = __mul__

    def inverse(self):
        if not self:
            raise ZeroDivisionError('zero exact field element')
        support = 0
        for index, value in enumerate(self.c):
            if value:
                support |= index
        if support == 0:
            return Field(1 / self.c[0])
        bit = 1 << (support.bit_length() - 1)
        conjugate = Field.from_coefficients(-x if i & bit else x for i, x in enumerate(self.c))
        norm = self * conjugate
        if any(x for i, x in enumerate(norm.c) if i & bit):
            raise ArithmeticError('quadratic conjugate norm did not descend')
        return conjugate * norm.inverse()

    def __truediv__(self, other):
        return self * Field(other).inverse()

    def __rtruediv__(self, other):
        return Field(other) / self

    def __pow__(self, exponent):
        if not isinstance(exponent, int) or exponent < 0:
            raise ValueError('nonnegative integer exponent required')
        result, base = Field(1), self
        while exponent:
            if exponent & 1:
                result = result * base
            base = base * base
            exponent //= 2
        return result


def positive_rational_root(value):
    """Positive root of a positive rational, if in this field; fail closed."""
    value = Field(value)
    if any(value.c[1:]) or value.c[0] <= 0:
        raise ValueError('positive rational radicand required')
    q = value.c[0]
    integer = q.numerator * q.denominator
    root = Field(1)
    for prime in (2, 3, 5):
        count = 0
        while integer % prime == 0:
            integer //= prime
            count += 1
        root *= prime ** (count // 2)
        if count % 2:
            root *= Field.root(prime)
    remaining = isqrt(integer)
    if remaining * remaining != integer:
        raise ValueError('radicand outside registered field')
    root *= Fraction(remaining, q.denominator)
    if root * root != value:
        raise ArithmeticError('root square mismatch')
    return root


def zeros(rows, columns):
    return [[Field(0) for _ in range(columns)] for _ in range(rows)]


def transpose(matrix):
    return [list(row) for row in zip(*matrix)]


def dot(left, right):
    if len(left) != len(right):
        raise ValueError('dot dimensions differ')
    return sum((Field(a) * Field(b) for a, b in zip(left, right) if a and b), Field(0))


def matmul(left, right):
    if not left or not right or len(left[0]) != len(right):
        raise ValueError('matrix dimensions differ')
    columns = transpose(right)
    return [[dot(row, column) for column in columns] for row in left]


def solve(matrix, rhs):
    """Deterministic first-nonzero-pivot elimination; verifies original residual."""
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix) or len(rhs) != size:
        raise ValueError('invalid exact system dimensions')
    width = len(rhs[0])
    if any(len(row) != width for row in rhs):
        raise ValueError('ragged right hand side')
    rows = [[Field(x) for x in matrix[i]] + [Field(x) for x in rhs[i]] for i in range(size)]
    for column in range(size):
        pivot = next((i for i in range(column, size) if rows[i][column]), None)
        if pivot is None:
            raise ArithmeticError('singular exact stationary system')
        rows[column], rows[pivot] = rows[pivot], rows[column]
        inverse = rows[column][column].inverse()
        rows[column] = [x * inverse for x in rows[column]]
        for i in range(column + 1, size):
            factor = rows[i][column]
            if factor:
                for j in range(column, size + width):
                    rows[i][j] -= factor * rows[column][j]
    result = zeros(size, width)
    for i in range(size - 1, -1, -1):
        for j in range(width):
            result[i][j] = rows[i][size + j] - sum((rows[i][k] * result[k][j] for k in range(i + 1, size) if rows[i][k]), Field(0))
    actual = matmul(matrix, result)
    if any(actual[i][j] != rhs[i][j] for i in range(size) for j in range(width)):
        raise ArithmeticError('exact original-system residual is nonzero')
    return result
