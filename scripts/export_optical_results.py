"""Export unique optical cases, 450/600 km comparison and readable PNGs."""

import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline
from space_debris_detection.plotting import publication_style, save_figure, plt

GROUPS = {"nominal":"Referencia", "phase":"Fase", "albedo":"Albedo", "fov":"FOV",
          "aperture":"Apertura", "velocity":"Velocidad"}


def main():
    root = Path(__file__).resolve().parents[1]
    source = root/"data/generated/optical"
    output = root/"outputs/optical/summary"
    manifest = json.loads((source/"manifest.json").read_text())
    book_path = root/"docs/references"/manifest["workbook"]
    baseline = load_baseline(book_path)
    if baseline.source_sha256 != manifest["workbook_sha256"]:
        raise ValueError("Regenerate the optical study after changing its workbook")
    model = OpticalModel(baseline)
    rows_by_key = {}
    def key(case, diameter):
        return tuple(asdict(case).values())+(round(diameter,14),)
    for group in GROUPS:
        for record in json.loads((source/f"range_vs_size_{group}.json").read_text()):
            case, diameter = StudyCase(**record["case"]), record["diameter_m"]
            identity = key(case,diameter)
            if identity not in rows_by_key:
                rows_by_key[identity] = {"case":case,"diameter_m":diameter,
                                         "intervals":record["intervals"],"groups":[]}
            elif rows_by_key[identity]["intervals"] != record["intervals"]:
                raise ValueError("Conflicting duplicate cases")
            rows_by_key[identity]["groups"].append(GROUPS[group])
    cases600 = list(rows_by_key.values())
    records = list(cases600)
    for record in cases600:
        case = replace(record["case"],observer_altitude_km=450.)
        records.append({"case":case,"diameter_m":record["diameter_m"],"groups":record["groups"],
                        "intervals":model.range_intervals(case,record["diameter_m"],manifest["range_grid_m"])})
    headers = ["Caso", "Familias de estudio", "Diámetro debris [cm]", "Fase [deg]", "Albedo geométrico",
        "FOV completo [deg]", "Apertura [mm]", "Velocidad transversal [km/s]", "Altitud observador [km]",
        "Tasa LVLH [rad/s]", "Exposición [ms]", "QE", "Transmisión óptica", "Píxel [µm]",
        "Sensor X [px]", "Sensor Y [px]", "Banda mínima [nm]", "Banda máxima [nm]",
        "PSF FWHM [px]", "Ruido lectura [e-/px]", "Dark [e-/px/s]", "Fondo AB [mag/arcsec²]",
        "Full well High Gain [e-/px]", "Umbral SNR lineal", "Focal [mm]", "Escala [arcsec/px]",
        "Número de intervalos", "Motivo límite inferior", "Estado límite superior", "Estado caso",
        "Alcance óptico mínimo [km]", "Alcance óptico máximo [km]"]
    table_rows, intervals_rows = [], []
    for j, record in enumerate(records,1):
        case, diameter, ivs = record["case"],record["diameter_m"],record["intervals"]
        focal, scale, _ = model.derived(case)
        lo,hi = (ivs[0]["lower_m"]/1000,ivs[-1]["upper_m"]/1000) if ivs else (None,None)
        record.update(id=f"OPT-{j:04d}",lower_km=lo,upper_km=hi)
        b=baseline
        table_rows.append([record['id'],"; ".join(record['groups']),diameter*100,case.phase_deg,case.albedo,
            case.fov_deg,case.aperture_m*1000,case.transverse_speed_m_s/1000,case.observer_altitude_km,
            case.frame_rate_rad_s,b['t_int']*1000,b['QE'],b['T_optics'],b['p_pixel']*1e6,
            b['N_x'],b['N_y'],b['lambda_min']*1e9,b['lambda_max']*1e9,b['PSF_FWHM'],b['sigma_read'],
            b['I_dark'],b['sky_background'],b['FWC_high_gain'],b['SNR_min'],focal*1000,scale*180*3600/np.pi,
            len(ivs),'; '.join(ivs[0]['lower_constraints']) if ivs else '',
            'Censurado: alcance >= valor indicado' if ivs and ivs[-1]['upper_censored'] else 'Resuelto' if ivs else 'Sin intervalo',
            'Varios intervalos: consultar hoja Intervalos' if len(ivs)>1 else 'Elegible' if ivs else 'No elegible',lo,hi])
        for k,iv in enumerate(ivs,1):
            intervals_rows.append([record['id'],k,iv['lower_m']/1000,iv['upper_m']/1000,
                                   iv['lower_censored'],iv['upper_censored'],'; '.join(iv['lower_constraints'])])
    # Comparative results pair identical physical cases; observer altitude alone changes.
    comparison = []
    for old,new in zip(cases600,records[len(cases600):]):
        delta = ((new['upper_km']/old['upper_km']-1)*100 if old['upper_km'] and new['upper_km']
                 and not old['intervals'][-1]['upper_censored'] and not new['intervals'][-1]['upper_censored'] else None)
        comparison.append([old['id'],new['id'],old['diameter_m']*100,old['case'].phase_deg,old['case'].albedo,
            old['case'].fov_deg,old['case'].aperture_m*1000,old['case'].transverse_speed_m_s/1000,
            old['lower_km'],new['lower_km'],old['upper_km'],new['upper_km'],delta,
            bool(old['intervals'] and old['intervals'][-1]['upper_censored']),
            bool(new['intervals'] and new['intervals'][-1]['upper_censored'])])
    wb=Workbook(); guide=wb.active; guide.title="Guía"
    for text in ["TRACE — resultados del estudio preliminar de detectabilidad óptica",
        f"{len(cases600)} casos únicos originales a 600 km; {len(cases600)} comparaciones nuevas a 450 km.",
        "Una fila = un tamaño y una configuración física. Duplicados de referencia entre familias consolidados.",
        "Las dos últimas columnas de Casos son alcance mínimo y máximo, en km.",
        "Son envolventes condicionales de SNR, full well, tránsito completo y modelo no resuelto; no detecciones de misión.",
        "Censurado: el valor máximo es el borde del barrido (20000 km); el alcance real puede ser mayor.",
        "Un caso con varios intervalos tiene huecos: no todo rango entre mínimo y máximo es elegible. Ver Intervalos.",
        "Casos sin detección llevan celdas de alcance vacías, nunca cero.",
        "Resumen_10cm contiene los mismos casos para 10 cm. Casos contiene todos los tamaños.",
        "Comparación: cambian solo altitud y giro LVLH; velocidad transversal, tamaño y óptica se mantienen iguales.",
        "No se calcula la nueva velocidad real de encuentro de una población al cambiar la órbita del observador.",
        "600 km es una hipótesis de ensayo; el flujo recibido a distancia y fase fijas no depende directamente de esa altitud.",
        "Orígenes: manifest.json y range_vs_size_*.json; baseline Excel SHA256: "+baseline.source_sha256]:
        guide.append([text])
    guide.column_dimensions['A'].width=125
    for cell in guide['A']:
        cell.alignment=Alignment(wrap_text=True,vertical='top');guide.row_dimensions[cell.row].height=34
    guide['A1'].font=Font(bold=True,size=15,color="17365D")
    def sheet(name,columns,rows):
        ws=wb.create_sheet(name);ws.append(columns)
        for row in rows:ws.append(row)
        ws.freeze_panes='D2';ws.sheet_view.showGridLines=False
        for col,title in enumerate(columns,1):
            ws.column_dimensions[get_column_letter(col)].width=min(42,max(15,len(title)*.75))
            ws.cell(1,col).alignment=Alignment(wrap_text=True,vertical='center')
        ws.row_dimensions[1].height=45
        if rows:
            table=Table(displayName=name.replace('_',''),ref=f"A1:{get_column_letter(len(columns))}{len(rows)+1}")
            table.tableStyleInfo=TableStyleInfo(name="TableStyleMedium2",showRowStripes=True)
            ws.add_table(table)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value,float):cell.number_format='0.000000000' if abs(cell.value)<.01 else '0.00'
        if 'Alcance óptico máximo [km]' in columns:
            for row in ws.iter_rows(min_row=2):
                for cell in row[-2:]:
                    cell.fill=PatternFill('solid',fgColor='E2EFDA');cell.font=Font(bold=True)
                if str(row[28].value).startswith('Censurado'):
                    row[-1].comment=Comment('Este valor es un límite inferior del alcance máximo: se alcanzó el final del barrido.','TRACE')
        return ws
    sheet('Resumen_10cm',headers,[r for r in table_rows if np.isclose(r[2],10)])
    sheet('Casos',headers,table_rows)
    sheet('Intervalos',['Caso','Intervalo','Mínimo [km]','Máximo [km]','Mínimo censurado','Máximo censurado','Causa inferior'],intervals_rows)
    sheet('Comparacion_altitud',['Caso 600 km','Caso 450 km','Diámetro [cm]','Fase [deg]','Albedo','FOV [deg]',
        'Apertura [mm]','Velocidad transversal [km/s]','Mínimo 600 [km]','Mínimo 450 [km]',
        'Máximo 600 [km]','Máximo 450 [km]','Cambio máximo [%]','Censurado 600','Censurado 450'],comparison)
    excel=source/'TRACE_Resultados_Estudio_Optico.xlsx';wb.save(excel)
    # Verify workbook structure and row count from the saved artifact.
    check=load_workbook(excel,read_only=True,data_only=True)
    assert check['Casos'].max_row==len(records)+1
    assert [c.value for c in next(check['Casos'].iter_rows())][-2:]==headers[-2:]
    check.close()
    publication_style()
    def case_label(case,group):
        return {'phase':f'{case.phase_deg:g}°','albedo':f'{case.albedo:g}',
                'fov':f'{case.fov_deg:g}°','aperture':f'{case.aperture_m*1000:g} mm',
                'velocity':f'{case.transverse_speed_m_s/1000:g} km/s'}[group]
    def window_dashboard(diameter_cm):
        xmax=max(r['upper_km'] for r in records if np.isclose(r['diameter_m'],diameter_cm/100) and r['upper_km'] is not None)
        fig,axes=plt.subplots(2,3,figsize=(13,8),layout='constrained')
        for ax,group in zip(axes.flat,list(GROUPS)[1:]+['altitude']):
            if group=='altitude':
                selected=[r for r in records if np.isclose(r['diameter_m'],diameter_cm/100) and
                          all(np.isclose(asdict(r['case'])[k],v) for k,v in manifest['nominal_instrument_case'].items() if k!='observer_altitude_km')]
                labels=[f"{r['case'].observer_altitude_km:g} km" for r in selected];title='Altitud del observador'
            else:
                selected=[r for r in cases600 if np.isclose(r['diameter_m'],diameter_cm/100) and GROUPS[group] in r['groups']]
                labels=[case_label(r['case'],group) for r in selected];title=GROUPS[group]
            for j,r in enumerate(selected):
                if r['lower_km'] is None:continue
                for iv in r['intervals']:
                    ax.plot([iv['lower_m']/1000,iv['upper_m']/1000],[j,j],color='#0072B2',lw=5,solid_capstyle='round')
                ax.plot(r['lower_km'],j,'o',color='#D55E00',ms=5)
                ax.text(r['upper_km']+xmax*.015,j,f"{'≥' if r['intervals'][-1]['upper_censored'] else ''}{r['upper_km']:.1f}",va='center',fontsize=9)
            ax.set(yticks=range(len(labels)),yticklabels=[f"{label} (mín. {r['lower_km']:.2f})" for label,r in zip(labels,selected)],
                   title=title,xlabel='Distancia [km]',xlim=(0,xmax*1.15))
            ax.invert_yaxis();ax.grid(axis='x',alpha=.25)
        fig.suptitle(f'TRACE — ventana óptica para objetos de {diameter_cm:g} cm',fontsize=16)
        fig.supxlabel('Línea azul: intervalo elegible; punto naranja: mínimo. Etiquetas en km. Una variable cambia por panel.\n'
                      'Referencia: 80 mm, FOV 14°, fase 60°, albedo 0,2, v⊥=5 km/s, 77 ms; resultados condicionales.',fontsize=10)
        save_figure(fig,output,f'trace_instrument_reference_{diameter_cm:g}cm_detection_windows')
    for diameter_cm in (1.,10.,100.):
        window_dashboard(diameter_cm)
    fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
    reference=manifest['nominal_instrument_case']
    reference_rows=[r for r in comparison if all(np.isclose(r[j],reference[k]) for j,k in
        ((3,'phase_deg'),(4,'albedo'),(5,'fov_deg'))) and np.isclose(r[6],reference['aperture_m']*1000)
        and np.isclose(r[7],reference['transverse_speed_m_s']/1000)]
    x=[r[2] for r in reference_rows]
    upper=[r[12] if r[12] is not None else np.nan for r in reference_rows]
    lower=[(r[9]/r[8]-1)*100 if r[8] and r[9] else np.nan for r in reference_rows]
    ax.semilogx(x,upper,label='Alcance máximo',color='#0072B2',marker='o',ms=3)
    ax.semilogx(x,lower,label='Alcance mínimo',color='#D55E00',marker='s',ms=3)
    ax.axhline(0,color='black',lw=.8)
    ax.set(xlabel='Diámetro del objeto [cm]',ylabel='Cambio al pasar de 600 a 450 km [%]',
           title='TRACE — efecto aislado de la altitud en el caso de referencia')
    ax.grid(alpha=.25);ax.legend()
    fig.supxlabel('Distancia de prueba y velocidad transversal constantes; solo cambia el giro LVLH.\n'
                  'Sin recálculo de encuentros ni cobertura; máximos censurados omitidos.',fontsize=9)
    save_figure(fig,output,'trace_instrument_reference_450_vs_600km_range_change')
    (output/'trace_instrument_reference_450_vs_600km_10cm.png').unlink(missing_ok=True)
    select=[r for r in comparison if np.isclose(r[2],10)]
    audit={'unique_cases_600km':len(cases600),'cases_450km':len(cases600),'total_rows':len(records),
           'excel':excel.name,'source_manifest_sha256':hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest(),
           'ten_cm_comparison':select,
           'frame_rate_600_rad_s':StudyCase(**manifest['nominal_instrument_case']).frame_rate_rad_s,
           'frame_rate_450_rad_s':replace(StudyCase(**manifest['nominal_instrument_case']),observer_altitude_km=450).frame_rate_rad_s}
    (source/'presentation_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='ten_cm_comparison'},indent=2))


if __name__=='__main__':main()
