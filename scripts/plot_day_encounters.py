"""Photometric encounter representatives and rigorous SNR-margin scatter plots."""
import argparse
import csv
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path

import numpy as np
from space_debris_detection.encounters import hermite_state,camera_axes_and_rate,solar_directions
from space_debris_detection.optical_validation import OpticalModel,StudyCase,load_baseline
from space_debris_detection.plotting import publication_style,save_figure,plt
from space_debris_detection.sensitivity import load_population
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


def evaluate_nodes(times,event,piece_indices,trajectory,pop,model,case,days0):
    """Photometry for exposure centres anywhere within one FoV encounter."""
    t=np.asarray(times);starts=trajectory['observer_t'][trajectory['piece_step'][piece_indices]]
    order=np.argsort(starts);piece_indices=np.asarray(piece_indices)[order];starts=starts[order]
    j=np.clip(np.searchsorted(starts,t,side='right')-1,0,len(starts)-1)
    pieces=piece_indices[j];steps=trajectory['piece_step'][pieces]
    t0=trajectory['observer_t'][steps];dt=trajectory['observer_t'][steps+1]-t0;s=np.clip((t-t0)/dt,0,1)
    r,v=hermite_state(trajectory['piece_r0'][pieces],trajectory['piece_v0'][pieces],
                     trajectory['piece_r1'][pieces],trajectory['piece_v1'][pieces],dt[:,None],s)
    ro,vo=hermite_state(trajectory['observer_r'][steps],trajectory['observer_v'][steps],
                       trajectory['observer_r'][steps+1],trajectory['observer_v'][steps+1],dt[:,None],s)
    delta=r-ro;distance=np.linalg.norm(delta,axis=1);los=delta/distance[:,None];relative=v-vo
    transverse=np.linalg.norm(relative-los*np.sum(los*relative,axis=1)[:,None],axis=1)
    axes,derivative=camera_axes_and_rate(ro,vo)
    body=np.einsum('ni,nij->nj',delta,axes)
    body_dot=np.einsum('ni,nij->nj',relative,axes)+np.einsum('ni,nij->nj',delta,derivative)
    omega=np.linalg.norm(body_dot-body*np.sum(body*body_dot,axis=1)[:,None]/distance[:,None]**2,axis=1)/distance
    sun=solar_directions(t,days0);along=np.sum(r*sun,axis=1)
    sunlit=(along>=0)|(np.linalg.norm(r-along[:,None]*sun,axis=1)>6371.)
    phase=np.degrees(np.arccos(np.clip(np.sum(-los*sun,axis=1),-1,1)))
    boresight_sun=np.degrees(np.arccos(np.clip(np.sum(axes[:,:,0]*sun,axis=1),-1,1)))
    solar_safe=boresight_sun>=model.b['sun_exclusion_min']
    closest=np.clip(-np.sum(ro*delta,axis=1)/distance**2,0,1)
    clear=np.linalg.norm(ro+closest[:,None]*delta,axis=1)>6371.
    half=np.array([model.b['W_x'],model.b['W_y']])/(2*model.derived(case)[0])
    in_fov=(body[:,0]>0)&np.all(np.abs(body[:,1:])<=body[:,0,None]*half+1e-5,axis=1)
    start,end=trajectory['event_start'][event],trajectory['event_end'][event]
    overlap=np.maximum(0,np.minimum(end,t+model.b['t_int']/2)-np.maximum(start,t-model.b['t_int']/2))
    overlap=np.minimum(overlap,model.b['t_int'])
    index=trajectory['event_object'][event]
    values=model.evaluate(case,distance*1000,diameter_m=pop['diameter_m'][index],
                          phase_deg=phase,apparent_rate_rad_s=omega,exposure_overlap_s=overlap)
    valid=in_fov & sunlit & clear & solar_safe & values['eligible']
    zero=model.evaluate(case,distance*1000,magnitude_ab=0.,phase_deg=phase,
                        apparent_rate_rad_s=omega,exposure_overlap_s=overlap)
    noise=values['pixels']*((values['background_e_per_pixel_s']+model.b['I_dark'])*model.b['t_int']+model.b['sigma_read']**2)
    q=model.b['SNR_min'];required=(q*q+np.sqrt(q**4+4*q*q*noise))/2
    m5=-2.5*np.log10(required/np.maximum(zero['signal_e'],1e-300))
    magnitude=values['magnitude_ab'];raw_margin=magnitude-m5
    # With no direct reflected solar signal, magnitude and margin are undefined.
    signal_possible=sunlit & clear
    return {'time_s':t,'range_km':distance,'transverse_speed_km_s':transverse,'angular_rate_rad_s':omega,
            'phase_deg':phase,'sunlit':sunlit,'earth_clear':clear,'solar_safe':solar_safe,'in_fov':in_fov,
            'visible':in_fov & sunlit & clear & solar_safe,'unresolved':values['unresolved'],
            'unsaturated':values['unsaturated'],'valid':valid,
            'snr':np.where(signal_possible,values['snr'],0.),
            'magnitude_ab':np.where(signal_possible,magnitude,np.nan),
            'limiting_magnitude_ab':m5,'magnitude_margin':np.where(valid,raw_margin,np.nan),
            'visible_time_s':overlap,'peak_pixel_e':values['peak_pixel_e']}


def best_node(result):
    # Stay inside the model domain; if none is valid choose a visible, then
    # geometric, representative. These excluded encounters remain in the table.
    score=np.where(result['valid'],result['snr'], -1.)
    if np.any(result['valid']):return int(np.argmax(score))
    if np.any(result['visible']):return int(np.argmax(np.where(result['visible'],result['snr'],-1.)))
    return len(result['time_s'])//2


def render_figures(rows,audit,root,tag,apparent_magnitude=False):
    propagation=audit['propagation']
    valid_count=sum(r['valid'] for r in rows)
    plotted_ids=len({r['object_id'] for r in rows if r['valid']})
    publication_style();colors={'1_to_5cm':'#0072B2','5_to_10cm':'#009E73','10cm_up':'#B57EDC'}
    labels={'1_to_5cm':r'$1\leq d<5$ cm','5_to_10cm':r'$5\leq d<10$ cm','10cm_up':r'$d\geq10$ cm'}
    valid=np.array([r['valid'] for r in rows])
    field='magnitude_ab' if apparent_magnitude else 'magnitude_margin'
    margin=np.array([r[field] for r in rows])
    finite=margin[valid]
    low=min(-1.,float(np.floor(finite.min()))-1) if len(finite) else -1.
    high=max(1.,float(np.ceil(finite.max()))+1) if len(finite) else 1.
    if apparent_magnitude and len(finite):
        low=float(np.floor(finite.min()))-1
        high=float(np.ceil(finite.max()))+1
    ymap=margin
    handles=[Line2D([0],[0],marker='o',ls='none',color=c,label=labels[g]) for g,c in colors.items()]
    handles += [Line2D([0],[0],marker=m,ls='none',color='#444444',label=label) for m,label in
                [('o','Primer cruce'),('x','Segundo cruce'),('^','Tercer cruce y posteriores')]]
    if not apparent_magnitude:
        handles += [Line2D([0],[0],color='red',ls='--',label='SNR = 5'),Patch(facecolor='red',alpha=.12,label='SNR < 5')]
    figure_names=[]
    for xfield,xlabel,suffix,log in [('range_km','Distancia observador–objeto [km]','range',True),
                                   ('transverse_speed_km_s',r'Velocidad relativa transversal $v_\perp$ [km/s]','transverse_velocity',False)]:
        fig,ax=plt.subplots(figsize=(10,7),layout='none');fig.subplots_adjust(left=.1,right=.98,bottom=.22,top=.79)
        if not apparent_magnitude:
            ax.axhspan(0,high,color='red',alpha=.12,zorder=0);ax.axhline(0,color='red',ls='--',lw=1.4)
        xs=np.array([r[xfield] for r in rows])
        for group,color in colors.items():
            for marker in ('o','x','^'):
                mask=valid & np.array([r['size_group']==group and r['marker']==marker for r in rows])
                ax.scatter(xs[mask],ymap[mask],c=color,marker=marker,s=9,alpha=.55,linewidths=.35,zorder=3)
        ylabel='Magnitud aparente AB [mag]' if apparent_magnitude else r'$m_{\mathrm{AB}}-m_{\mathrm{AB},\,\mathrm{SNR}=5}$ [mag]'
        ax.set(xlabel=xlabel,ylabel=ylabel,
               ylim=(low,high),title=f'TRACE — cruces por el campo en {propagation["duration_s"]/3600:g} h · SSO 450 km')
        if log:ax.set_xscale('log')
        ax.grid(which='major',alpha=.35,lw=.5);ax.grid(which='minor',alpha=.2,lw=.3)
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.995),ncol=3,frameon=False,fontsize=8)
        common=(f'{propagation["population_count"]} objetos propagados; {valid_count} cruces válidos de {plotted_ids} objetos. SSO LTAN 06:00, i=97,1877°.\n'
            f'Intervalo UTC: {propagation["epoch0"]} + {propagation["duration_s"]/3600:g} h. D=80 mm, FOV=14°, 77 ms, albedo=0,2; gravedad central + J2.\n')
        if apparent_magnitude:
            caption='Un punto por cruce, en su instante representativo guardado. Solo cruces válidos por el FoV.\nLos colores indican tamaño y los símbolos el ordinal de cruce de cada objeto durante el día.'
        else:
            caption=('Un punto por cruce: mejor SNR válido encontrado. Solo cruces por el FoV dentro del dominio del modelo.\n'
                     'Debajo de cero: SNR ≥ 5 dentro del dominio válido. Los símbolos cuentan cruces de cada objeto, no exposiciones.')
        fig.supxlabel(common+caption,fontsize=8,y=.015)
        prefix='apparent_magnitude' if apparent_magnitude else 'magnitude_margin'
        fig_name='trace_nominal_'+tag+'_'+prefix+'_vs_'+suffix;figure_names.append(fig_name+'.png')
        save_figure(fig,root/'outputs/optical/summary',fig_name)
    key='apparent_magnitude_figures' if apparent_magnitude else 'figures'
    audit[key]=figure_names
    if apparent_magnitude:
        audit['apparent_magnitude_plot']='same valid crossings and representative times; raw magnitude_ab; no SNR line, shading or detection labels'
    audit['plot_exclusions']='excluded events omitted from figures; retained in complete encounter CSV'
    audit['plotted_events']=valid_count
    audit['plotted_distinct_objects']=plotted_ids
    return audit


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='sso450km_24h')
    parser.add_argument('--sample',type=float,default=.25);parser.add_argument('--suffix',default='')
    parser.add_argument('--plots-only',action='store_true')
    parser.add_argument('--apparent-magnitude',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];source=root/'data/generated/encounters'
    if args.plots_only:
        name=args.tag+args.suffix
        audit=json.loads((source/(name+'_photometry.json')).read_text())
        with (source/(name+'_encounters.csv')).open() as f:
            rows=list(csv.DictReader(f))
        for row in rows:
            row['valid']=row['valid']=='True'
            for field in ('magnitude_margin','magnitude_ab','range_km','transverse_speed_km_s'):
                row[field]=float(row[field]) if row[field] else np.nan
        audit=render_figures(rows,audit,root,args.tag,apparent_magnitude=args.apparent_magnitude)
        (source/(name+'_photometry.json')).write_text(json.dumps(audit,indent=2)+'\n')
        figure_key='apparent_magnitude_figures' if args.apparent_magnitude else 'figures'
        print(json.dumps({k:audit[k] for k in ('plotted_events','plotted_distinct_objects',figure_key)},indent=2))
        return
    propagation=json.loads((source/(args.tag+'_propagation.json')).read_text())
    with np.load(source/(args.tag+'_trajectories.npz')) as archive:
        tr={name:archive[name] for name in archive.files}
    case=StudyCase(**propagation['instrument'])
    path=root/'data/generated/trace_population_50000.csv';pop=load_population(path)
    baseline=load_baseline(next((root/'docs/references').glob('*.xlsx')))
    if baseline.source_sha256!=propagation['baseline_sha256']:raise ValueError('Stale baseline')
    model=OpticalModel(baseline)
    epoch=datetime.fromisoformat(propagation['epoch0'].replace('Z','+00:00'))
    days0=(epoch-datetime(2000,1,1,12,tzinfo=timezone.utc)).total_seconds()/86400
    buckets=[[] for _ in tr['event_object']]
    for piece,event in enumerate(tr['piece_event']):buckets[event].append(piece)
    rows=[]
    for event,(start,end,index) in enumerate(zip(tr['event_start'],tr['event_end'],tr['event_object'])):
        # Sampling seeks a good exposure centre, not a single instant per step.
        n=max(17,int(np.ceil((end-start)/args.sample))+1)
        times=np.linspace(start,end,n)
        # Insert the complete-exposure edges, midpoint and all interpolation knots.
        extras=[start+baseline['t_int']/2,end-baseline['t_int']/2,(start+end)/2]
        extras.extend(tr['observer_t'][tr['piece_step'][buckets[event]]].tolist())
        extras=np.asarray(extras);extras=extras[(extras>=start)&(extras<=end)]
        times=np.unique(np.r_[times,extras])
        result=evaluate_nodes(times,event,buckets[event],tr,pop,model,case,days0)
        k=best_node(result);t=times[k]
        left=times[max(0,k-1)];right=times[min(len(times)-1,k+1)]
        fine=np.linspace(left,right,65)
        refine=evaluate_nodes(fine,event,buckets[event],tr,pop,model,case,days0)
        j=best_node(refine)
        # Keep an already valid representative if refinement only lands outside.
        if not result['valid'][k] or (refine['valid'][j] and refine['snr'][j]>=result['snr'][k]):result,k=refine,j
        best={name:values[k].item() for name,values in result.items()}
        cm=float(pop['diameter_m'][index]*100)
        row={'encounter_id':f'PASS-{event+1:06d}','object_id':pop['object_id'][index],
             'object_index':int(index),'crossing_number':int(tr['event_ordinal'][event]),
             'marker':('o' if tr['event_ordinal'][event]==1 else 'x' if tr['event_ordinal'][event]==2 else '^'),
             'diameter_cm':cm,'size_group':('1_to_5cm' if cm<5 else '5_to_10cm' if cm<10 else '10cm_up'),
             'entry_s':float(start),'exit_s':float(end),'duration_s':float(end-start),
             'truncated_start':bool(start<1e-6),'truncated_end':bool(end>=propagation['duration_s']-1e-6),
             **best,'snr_ge_5':bool(best['valid'] and best['snr']>=5)}
        row['epoch_utc']=(epoch+timedelta(seconds=row['time_s'])).isoformat().replace('+00:00','Z')
        rows.append(row)
        if (event+1)%2000==0:print(json.dumps({'photometry_passes':event+1}),flush=True)
    name=args.tag+args.suffix
    with (source/(name+'_encounters.csv')).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader()
        for row in rows:writer.writerow({k:('' if isinstance(v,float) and not np.isfinite(v) else v) for k,v in row.items()})
    # Margin and actual SNR must give the same classification in the valid domain.
    for row in rows:
        if row['valid']:assert (row['magnitude_margin']<=1e-12)==(row['snr']>=5-1e-12)
    audit={'propagation':propagation,'photometry_base_sampling_s':args.sample,'local_refinement_points':65,
           'representative':'largest valid SNR found per crossing; local refinement; no fixed exposure cadence imposed',
           'events':len(rows),'distinct_objects':len({r['object_id'] for r in rows}),
           'valid_domain_events':sum(r['valid'] for r in rows),'visible_representatives':sum(r['visible'] for r in rows),
           'snr_ge_5_events':sum(r['snr_ge_5'] for r in rows),
           'distinct_snr_ge_5_objects':len({r['object_id'] for r in rows if r['snr_ge_5']}),
           'markers':{m:sum(r['marker']==m for r in rows) for m in ('o','x','^')},
           'size_groups':{g:sum(r['size_group']==g for r in rows) for g in ('1_to_5cm','5_to_10cm','10cm_up')},
           'excluded_events':sum(not r['valid'] for r in rows),
           'normalization':'m_AB - m_AB(SNR=5), per exposure geometry, noise pixels and actual visible time',
           'plot_exclusions':'shadow, Earth occultation, solar exclusion, saturation or resolved sources are categorical, not assigned a fake margin',
           'exposure':'77 ms exposure centred at selected instant; actual entry/exit truncation for partial passes',
           'revisits':'chronological FoV passages per ID, including excluded passages; not individual exposures'}
    (source/(name+'_photometry.json')).write_text(json.dumps(audit,indent=2)+'\n')
    if args.suffix:print(json.dumps({k:v for k,v in audit.items() if k!='propagation'},indent=2));return
    audit=render_figures(rows,audit,root,args.tag,apparent_magnitude=args.apparent_magnitude)
    (source/(name+'_photometry.json')).write_text(json.dumps(audit,indent=2)+'\n')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==propagation['population_sha256']
    print(json.dumps({k:v for k,v in audit.items() if k!='propagation'},indent=2),flush=True)


if __name__=='__main__':main()
