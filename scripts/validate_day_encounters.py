"""Validate day encounter convergence after running the two optional refinements."""
import csv
import json
from pathlib import Path
import numpy as np


def main():
    root=Path(__file__).resolve().parents[1];source=root/'data/generated/encounters'
    def read(name):
        with (source/name).open() as f:return list(csv.DictReader(f))
    rows=read('sso450km_24h_encounters.csv')
    refined=read('sso450km_24h_refinement_check_encounters.csv')
    assert len(rows)==len(refined)
    assert [r['snr_ge_5'] for r in rows]==[r['snr_ge_5'] for r in refined]
    assert [r['valid'] for r in rows]==[r['valid'] for r in refined]
    with np.load(source/'sso450km_24h_trajectories.npz') as a,np.load(source/'validation_5000_step10_trajectories.npz') as b:
        mask=a['event_object']<5000
        reference={(int(i),int(o)):(s,e) for i,o,s,e in zip(b['event_object'],b['event_ordinal'],b['event_start'],b['event_end'])}
        assert int(mask.sum())==len(reference)
        errors=[]
        for i,o,s,e in zip(a['event_object'][mask],a['event_ordinal'][mask],a['event_start'][mask],a['event_end'][mask]):
            s1,e1=reference[int(i),int(o)];errors.append([abs(s-s1),abs(e-e1)])
        errors=np.asarray(errors)
        check={'subset_objects':5000,'coarse_step_s':20,'fine_step_s':10,
               'coarse_events':int(mask.sum()),'fine_events':len(reference),
               'max_entry_time_difference_s':float(errors[:,0].max()),'max_exit_time_difference_s':float(errors[:,1].max()),
               'median_max_edge_difference_s':float(np.median(errors.max(axis=1))),
               'coarse_minimum_duration_s':float(np.min(a['event_end']-a['event_start'])),
               'photometry_refinement':{'base_step_s':.25,'refined_step_s':.125,
                  'same_event_detection_flags':True,'same_event_validity_flags':True,
                  'snr5_events_both':sum(r['snr_ge_5']=='True' for r in rows),
                  'unique_snr5_objects_both':len({r['object_id'] for r in rows if r['snr_ge_5']=='True'})},
               'max_observer_position_difference_m':float(np.linalg.norm(a['observer_r']-b['observer_r'][::2],axis=1).max()*1000),
               'observer_altitude_min_km':float(np.linalg.norm(a['observer_r'],axis=1).min()-6371),
               'observer_altitude_max_km':float(np.linalg.norm(a['observer_r'],axis=1).max()-6371)}
    counts={};ends={}
    for r in rows:
        ident=r['object_id'];counts[ident]=counts.get(ident,0)+1
        assert int(r['crossing_number'])==counts[ident]
        assert float(r['entry_s'])<=float(r['time_s'])<=float(r['exit_s'])
        if ident in ends:assert ends[ident]<float(r['entry_s'])
        ends[ident]=float(r['exit_s'])
        assert r['marker']==('o' if counts[ident]==1 else 'x' if counts[ident]==2 else '^')
        if r['valid']=='True':assert (float(r['magnitude_margin'])<=0)==(float(r['snr'])>=5)
        else:assert r['magnitude_margin']==''
    check.update(numbering_and_margin_classification_verified_for_all_events=True,
        max_crossings_per_object=max(counts.values()),
        partial_exposure_representatives=sum(float(r['visible_time_s'])<.077-1e-10 for r in rows),
        boundary_truncated_events=sum(r['truncated_start']=='True' or r['truncated_end']=='True' for r in rows),
        detections_by_size={g:sum(r['size_group']==g and r['snr_ge_5']=='True' for r in rows)
                           for g in ('1_to_5cm','5_to_10cm','10cm_up')})
    (source/'sso450km_24h_validation.json').write_text(json.dumps(check,indent=2)+'\n')
    print(json.dumps(check,indent=2))


if __name__=='__main__':main()
