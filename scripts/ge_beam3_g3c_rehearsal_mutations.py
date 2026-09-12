"""Deterministic negative fixtures only. No packet is a positive authority."""
import copy
import math
from hashlib import sha256
import ge_beam3_g3c_restart_preflight as p
import ge_beam3_g3c_rehearsal_contract as design
import ge_beam3_g3c_rehearsal_bridge_contract as bridge_contract


def different_hash(value):
    p.hash_value(value)
    return ('0' if value[0]!='0' else '1')+value[1:]


def repair(value):
    """Repair available outer commitments; never invent earlier payloads."""
    for row in value['final_state']['native_rows']:
        body=row['payload']; body['state_sha256']=p.digest({k:v for k,v in body.items() if k!='state_sha256'})
    value['final_sha256']=p.digest(value['final_state'])
    if value['history']:
        value['history'][-1]['accepted_state_sha256']=value['final_sha256']
    previous=None
    for row in value['history']:
        row['previous_entry_sha256']=previous; previous=p.digest(row)
    return value


def coherent_pose(value, member):
    _,source=p.authorities()
    g=source.expand(value['definition']['fixture_id'],'BASE',value['definition']['common_motion'])[1]['graph']
    state=value['final_state']; ids=[n for n,_ in g['nodes']]
    # Alter an actual native node, then propagate every corresponding copy.
    node=next(e['nodes'][0] for e in g['elements'] if e['family']=='NATIVE'); index=ids.index(node)
    if member=='total_u': state['total_u'][6*index]=math.nextafter(state['total_u'][6*index],math.inf)
    else:
        Q=state['rotations'][index]
        state['rotations'][index]=[[-x for x in Q[1]],list(Q[0]),list(Q[2])]
    elements={e['id']:e for e in g['elements']}
    for row in state['native_rows']:
        inds=[ids.index(n) for n in elements[row['element_id']]['nodes']]
        row['payload']['committed_total_u']=[state['total_u'][6*i+j] for i in inds for j in range(6)]
        row['payload']['committed_nodal_rotation_matrices']=[copy.deepcopy(state['rotations'][i]) for i in inds]
    for row in state['adapter_rows']:
        nodes=elements[row['element_id']]['nodes']; inds=[ids.index(n) for n in nodes]
        row['pose_sha256']=p.digest(dict(node_ids=nodes,total_translations=[state['total_u'][6*i:6*i+3] for i in inds],rotations=[state['rotations'][i] for i in inds]))


def packet_attack(raw, category, member):
    """Return changed packet and exact expected diagnostic; special reads separate."""
    allowed={(r['id'],m) for r in design.parent()['mutation_categories'] for m in r['members']}
    if (category,member) not in allowed: raise ValueError('unregistered mutation')
    value=p.strict(raw); state=value['final_state']; native=state['native_rows'][0]
    body=native['payload']; response=body['response']; adapter=state['adapter_rows'][0]
    history=value['history']
    if len(history) not in (2,9): raise ValueError('authentic origin prefix required')
    error=None; late=None
    if category=='R01_DUPLICATE_KEYS':
        # Duplicate an existing key at exactly the selected nested location.
        target={'top':value,'native_payload':body,'history_entry':history[0]}[member]
        key=next(iter(target)); fragment=p.canonical(target).rstrip(b'\n')
        duplicate=b'{'+p.canonical({key:target[key]}).rstrip(b'\n')[1:-1]+b','+fragment[1:]
        changed=raw.replace(fragment,duplicate,1)
        error='duplicate JSON key'
    elif category=='R02_NONFINITE_OVERFLOW':
        marker=b'"runtime_sha256":'+p.canonical(value['runtime_sha256']).rstrip(b'\n')
        changed=raw.replace(marker,b'"runtime_sha256":'+member.encode(),1)
        error='Out of range float values are not JSON compliant: inf' if member=='1e999' else 'nonfinite JSON'
    elif category=='R05_BOUNDS_AND_SHAPES' and member=='bytes_above_8MiB':
        changed=b' '*(8*1024**2+1); error='external checkpoint digest mismatch'
    else:
        if category=='R03_UNKNOWN_KEYS':
            {'top':value,'state':state,'native_full':response['full'],'adapter':adapter}[member]['UNREGISTERED']=False
            error='checkpoint schema' if member=='top' else 'exact '+{'state':'state','native_full':'native_full','adapter':'adapter_row'}[member]+' schema'
        elif category=='R04_EXACT_NUMERIC_TYPES':
            if member=='bool_epoch': state['epoch']=True; error='bounded integer'
            elif member=='bool_element_id': native['element_id']=True; error='positive integer required'
            else: state['total_u'][0]=0; error='finite binary64 array leaf required'
        elif category=='R05_BOUNDS_AND_SHAPES':
            if member=='history_above_128': value['history']=[copy.deepcopy(history[0]) for _ in range(129)]; error='history bound'
            elif member=='native_42_shape': response['full']['residual'].pop(); error='array shape'
            else: state['total_u'].pop(); error='array shape'
        elif category=='R06_OLD_SCHEMA':
            value['schema']=bridge_contract.source_literals()[member]
            error='literal schema'
        elif category=='R07_SELECTOR':
            key={'unknown_graph':'fixture_id','unknown_variant':'variant','unknown_motion':'common_motion'}[member]
            value['definition'][key]='UNREGISTERED'; error='enum' if member=='unknown_motion' else 'unregistered graph/variant/motion'
        elif category=='R08_POLICY_FIXTURE':
            if member=='wrong_owner_policy': value['policy']='UNREGISTERED'; error='literal policy'
            elif member=='well_shaped_native_element_identity': body['element_identity']=different_hash(body['element_identity'])
            else:
                key='fixture_sha256' if member=='wrong_fixture_sha' else 'policy_sha256'
                value['definition'][key]=different_hash(value['definition'][key]); error='definition authority mismatch'
        elif category=='R09_RUNTIME':
            if member=='changed_implementation_review': raise ValueError('runner review attack is not a packet mutation')
            value['runtime_sha256']=different_hash(value['runtime_sha256']); error='runtime authority mismatch'
        elif category=='R10_NORMAL_SOURCE': raise ValueError('source read attack is not a packet mutation')
        elif category=='R11_ELEMENT_ID_ORDER':
            if member=='native_id': native['element_id']+=1
            elif member=='adapter_id': adapter['element_id']=999999; error='unregistered adapter'
            elif member=='duplicate_id': state['native_rows'][1]['element_id']=native['element_id']
            else: state['native_rows'].reverse()
            error=error or 'element order/identity'
        elif category=='R12_EPOCH':
            if member=='gap': state['epoch']+=1; error='definition/epoch link'
            elif member=='negative': state['epoch']=-1; error='bounded integer'
            else: body['epoch']+=1; error='native epoch/link'
        elif category=='R13_COMMANDS':
            if member=='reordered':
                history[0]['command'],history[1]['command']=history[1]['command'],history[0]['command']
                error='preparation sequence' if value['definition']['common_motion']=='CM3' else 'root stage sequence'
            elif member=='omitted_preparation':
                if value['definition']['common_motion']=='NONE':
                    value['definition']['common_motion']='CM3'
                    value['definition_sha256']=p.digest(value['definition']); state['definition_sha256']=value['definition_sha256']
                else:
                    del history[0]
                    state['epoch']=len(history)
                    for row in state['native_rows']: row['payload']['epoch']=len(history)
                    for row in state['adapter_rows']: row['epoch']=len(history)
                    for i,row in enumerate(history): row['epoch']=i+1
                    history[0]['origin_sha256']=value['initial_sha256']
                error='preparation sequence'
            elif member=='force_scale_switch':
                history[-1]['command']['force_scale']=1.; error='changed force scale inside program'
            else: history[-1]['command']['root_stage']=3 if len(history)==2 else 2; error='root stage sequence'
        elif category=='R14_HISTORY_LINKS':
            key={'previous_entry':'previous_entry_sha256','origin':'origin_sha256','accepted_state':'accepted_state_sha256'}[member]
            # Apply AFTER ordinary repair so the target link remains broken.
            late=lambda: history[-1].__setitem__(key,different_hash(history[-1][key]))
            error='final journal link' if member=='accepted_state' else 'journal linkage'
        elif category=='R15_FINAL_STATE_LINK':
            if member=='final_state_previous': state['previous_sha256']=different_hash(state['previous_sha256'])
            else: late=lambda: history[-1].__setitem__('accepted_state_sha256',different_hash(history[-1]['accepted_state_sha256']))
            error='final journal link'
        elif category=='R16_OUTER_STATE_HASHES':
            if member=='initial_sha':
                value['initial_sha256']=different_hash(value['initial_sha256']); history[0]['origin_sha256']=value['initial_sha256']
                error='genuine virgin state mismatch'
            else: late=lambda: value.__setitem__('final_sha256',different_hash(value['final_sha256'])); error='final state hash'
        elif category=='R17_NATIVE_FULL_RESIDUAL': response['full']['residual'][0]=math.nextafter(response['full']['residual'][0],math.inf)
        elif category=='R18_NATIVE_FULL_JACOBIAN': response['full']['jacobian'][0][0]=math.nextafter(response['full']['jacobian'][0][0],math.inf)
        elif category=='R19_NATIVE_SCHUR':
            array=response[{'lift':'lift','correction':'correction','condensed_tangent':'tangent','condensed_residual':'residual'}[member]]
            if type(array[0]) is list: array[0][0]=math.nextafter(array[0][0],math.inf)
            else: array[0]=math.nextafter(array[0],math.inf)
        elif category=='R20_NATIVE_POSE':
            if member=='improper_Q':
                body['committed_nodal_rotation_matrices'][0][0]=[-x for x in body['committed_nodal_rotation_matrices'][0][0]]; error='proper rotation required'
            else: coherent_pose(value,member)
        elif category=='R21_NATIVE_LOADS':
            body['line' if member=='nonzero_line' else 'couple'][0]=1.; error='finite binary64 array leaf required'
        elif category=='R22_ADAPTER_FIELDS':
            if member=='pose_sha': adapter['pose_sha256']=different_hash(adapter['pose_sha256']); error='adapter pose hash'
            else: adapter['deformation'][0]=math.nextafter(adapter['deformation'][0],math.inf)
        elif category=='R23_ADAPTER_DIAGNOSTIC':
            key={'candidate_sha':'diagnostic_sha256','origin_sha':'origin_sha256','previous_sha':'previous_sha256','well_shaped_adapter_definition_sha256':'definition_sha256'}[member]
            adapter[key]=different_hash(adapter[key]); error='adapter origin/link' if member=='origin_sha' else None
        elif category=='R24_SOURCE_FLAGS': adapter[member]=True; error='literal '+member
        else: raise ValueError('missing mutation constructor')
        repair(value)
        if late is not None: late()
        changed=p.canonical(value)
    if changed==raw: raise ValueError('no-op mutation forbidden')
    if design.rejection(category,member)=='GENUINE_REPLAY_MISMATCH':
        error='genuine replay prefix mismatch: '+str(len(history))
    if error is None: raise ValueError('missing exact rejection diagnostic')
    return changed,dict(category=category,member=member,rejection=design.rejection(category,member),
                        expected_error=error,before_sha256=sha256(raw).hexdigest(),after_sha256=sha256(changed).hexdigest())


def attack_fixture(raw,category,member,review):
    """Derive exact expected negative bytes/identity from bound original input."""
    if category=='R10_NORMAL_SOURCE':
        path=p.ROOT/(p.DEFINITION if member=='mocked_source_hash' else 'docs/reference_cases/ge_beam3_g3c_fixtures_v1.json')
        original=path.read_bytes(); changed=original+b'\n# negative read fixture\n'
        error='external runtime mismatch' if member=='mocked_source_hash' else 'frozen authority changed: docs/reference_cases/ge_beam3_g3c_fixtures_v1.json'
        record=dict(source_path=str(path))
    elif (category,member)==('R09_RUNTIME','changed_implementation_review'):
        original=p.canonical(review); value=p.strict(original); value['subject_commit']='0'*40
        changed=p.canonical(value); error='implementation review hash mismatch'; record={}
    else: return packet_attack(raw,category,member)
    if changed==original: raise ValueError('no-op authority attack')
    record.update(category=category,member=member,rejection=design.rejection(category,member),
                  expected_error=error,before_sha256=sha256(original).hexdigest(),after_sha256=sha256(changed).hexdigest())
    return changed,record
