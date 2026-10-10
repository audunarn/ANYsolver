"""Explicit control-lift S3 mesh-friction path, unchanged physical fixture."""
from dataclasses import replace
import argparse,json
from pathlib import Path
from examples.general_contact_s3_mesh_moving_friction import build_case as _original_case,solve_case


def build_case():
    case=list(_original_case())
    case[2]=replace(case[2],path_predictor='control_projection_dev')
    return tuple(case)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--through-step',type=int,default=6,choices=range(1,7))
    parser.add_argument('--restart',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    restart=json.loads(args.restart.read_text()) if args.restart else None
    result=solve_case(build_case(),args.through_step,restart)
    args.output.write_text(json.dumps(dict(status=result.status,info=result.info,
        checkpoint=result.to_restart_checkpoint() if result.status=='completed' else None),
        default=lambda x:x.tolist() if hasattr(x,'tolist') else x.item(),indent=2))
    if result.status!='completed':raise RuntimeError(result.info)


if __name__=='__main__':main()
