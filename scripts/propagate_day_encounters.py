"""Propagate the full nominal population and collect all interpolated FoV passes."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from space_debris_detection.encounters import (rk4_j2,camera_coordinates,field_candidate_indices,
                                               hermite_coefficients,field_intervals)
from space_debris_detection.optical_validation import OpticalModel,StudyCase,load_baseline
from space_debris_detection.orbits import elements_to_states
from space_debris_detection.sensitivity import load_population


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--step',type=float,default=20.)
    parser.add_argument('--duration',type=float,default=86400.)
    parser.add_argument('--limit',type=int,default=50000)
    parser.add_argument('--tag',default='sso450km_24h');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];out=root/'data/generated/encounters';out.mkdir(exist_ok=True)
    source=root/'data/generated/optical';reference=json.loads((source/'sso_observer_audit.json').read_text())
    case=StudyCase(**reference['instrument']);scenario=reference['selected_sso_scenario']
    manifest=json.loads((source/'manifest.json').read_text())
    baseline=load_baseline(root/'docs/references'/manifest['workbook']);model=OpticalModel(baseline)
    path=root/'data/generated/trace_population_50000.csv';sha=hashlib.sha256(path.read_bytes()).hexdigest()
    pop=load_population(path);count=args.limit
    if not (args.step>0 and args.duration>0 and 1<=count<=len(pop['object_id'])):
        raise ValueError('Positive step/duration and a valid population limit required')
    position=np.column_stack([pop[k][:count] for k in ('x_km','y_km','z_km')])
    velocity=np.column_stack([pop[k][:count] for k in ('vx_km_s','vy_km_s','vz_km_s')])
    ro,vo=elements_to_states(scenario['semi_major_axis_km'],0,scenario['inclination_deg'],scenario['raan_deg'],0,0)
    position=np.vstack((position,ro));velocity=np.vstack((velocity,vo))
    half=np.array([baseline['W_x'],baseline['W_y']])/(2*model.derived(case)[0])
    body,body_rate=camera_coordinates(position[:-1],velocity[:-1],position[-1],velocity[-1])
    observer_r=[ro.copy()];observer_v=[vo.copy()];observer_t=[0.]
    active={};events=[];pieces=[];candidate_total=0;tic=time.monotonic();t=0.;step=0
    while t<args.duration-1e-9:
        dt=min(args.step,args.duration-t)
        end_r,end_v=rk4_j2(position,velocity,dt)
        end_body,end_rate=camera_coordinates(end_r[:-1],end_v[:-1],end_r[-1],end_v[-1])
        indices=field_candidate_indices(body,body_rate,end_body,end_rate,dt,half)
        candidate_total+=len(indices);continued=set()
        for index in indices:
            coefficients=hermite_coefficients(body[index],body_rate[index],end_body[index],end_rate[index],dt)
            intervals=field_intervals(coefficients,half)
            previous=active.get(int(index))
            for lo,hi in intervals:
                enter,leave=t+lo*dt,t+hi*dt
                if previous is None or abs(previous['end_s']-enter)>1e-5:
                    previous={'object_index':int(index),'start_s':enter,'end_s':leave,'pieces':[]}
                    events.append(previous)
                previous['end_s']=leave
                piece=len(pieces)
                pieces.append((step,int(index),lo,hi,position[index].copy(),velocity[index].copy(),
                               end_r[index].copy(),end_v[index].copy()))
                previous['pieces'].append(piece)
                if hi>=1-1e-10:
                    active[int(index)]=previous;continued.add(int(index))
                else:active.pop(int(index),None)
            if not intervals:active.pop(int(index),None)
        for index in list(active):
            if index not in continued:active.pop(index)
        position,velocity=end_r,end_v;body,body_rate=end_body,end_rate
        t+=dt;step+=1
        observer_r.append(position[-1].copy());observer_v.append(velocity[-1].copy());observer_t.append(t)
        if step%120==0:
            print(json.dumps({'elapsed_hours':round(t/3600,2),'passes':len(events),'pieces':len(pieces),
                              'wall_s':round(time.monotonic()-tic,1)}),flush=True)
    # Sort independent encounters chronologically and number each object's passes.
    order=sorted(range(len(events)),key=lambda j:(events[j]['start_s'],events[j]['object_index']))
    events=[events[j] for j in order];ordinals={}
    event_index=np.empty(len(pieces),dtype=np.int32)
    for j,event in enumerate(events):
        index=event['object_index'];ordinals[index]=ordinals.get(index,0)+1
        event['crossing_number']=ordinals[index]
        for piece in event['pieces']:event_index[piece]=j
    np.savez_compressed(out/(args.tag+'_trajectories.npz'),
        observer_t=np.array(observer_t),observer_r=np.array(observer_r),observer_v=np.array(observer_v),
        piece_step=np.array([p[0] for p in pieces],dtype=np.int32),
        piece_object=np.array([p[1] for p in pieces],dtype=np.int32),
        piece_lo=np.array([p[2] for p in pieces]),piece_hi=np.array([p[3] for p in pieces]),
        piece_r0=np.array([p[4] for p in pieces]),piece_v0=np.array([p[5] for p in pieces]),
        piece_r1=np.array([p[6] for p in pieces]),piece_v1=np.array([p[7] for p in pieces]),
        piece_event=event_index,event_object=np.array([e['object_index'] for e in events]),
        event_start=np.array([e['start_s'] for e in events]),event_end=np.array([e['end_s'] for e in events]),
        event_ordinal=np.array([e['crossing_number'] for e in events]))
    audit={'population_sha256':sha,'baseline_sha256':baseline.source_sha256,'epoch0':reference['epoch0'],
           'duration_s':args.duration,'step_s':args.step,'population_count':count,'observer':scenario,
           'instrument':reference['instrument'],'events':len(events),'pieces':len(pieces),
           'distinct_objects':len(ordinals),'candidate_segments':candidate_total,
           'propagation':'Cartesian RK4 with central gravity + J2 for observer and every debris',
           'J2':1.08262668e-3,'J2_reference_radius_km':6378.137,
           'crossings':'cubic Hermite in rotating camera; Bernstein conservative candidate bounds; all polynomial face roots',
           'frame':'fixed nominal TEME axes treated as inertial, approximate Sun in same axes',
           'not_modelled':['drag','higher harmonics','third bodies','Earth orientation/nutation corrections','penumbra','self shadow'],
           'truncated_passes':'passes intersecting start/end are counted and flagged by their boundary time',
           'runtime_s':time.monotonic()-tic}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    (out/(args.tag+'_propagation.json')).write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2),flush=True)


if __name__=='__main__':main()
