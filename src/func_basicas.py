import pyart
import math
import numpy as np
import os

def getFileNames(path):
    files = []
    try:
        for r, d, f in os.walk(path):
            for file in f:
                if '.nc' in file:
                    files.append(os.path.join(r, file))
        files.sort()
    except:
        print('[ERROR] Problemas al acceder al PATH especificado!')
        return -1
    return files

def getRadars(files,vol_completo = True, sweep = 0):
    radares = []
    for f in files: 
        try:
            if vol_completo:
                radares.append(pyart.io.read(f))
            else:
                radares.append(pyart.io.read(f).extract_sweeps([sweep]))

            print('Archivo '+ f.split('/')[-1][:-3] + ' cargado!')
        except TypeError:
            print('[ERROR] Problema al decodificar '+ f.split('/')[-1])
            return -1
    return radares

def calcular_zdr(radar):
    if 'TH' and'TV' in radar.fields.keys():
        TDRc = np.zeros((radar.nrays,radar.ngates))
        # Solo uso datos que tengan buena calidad para el calculo
        if 'RHOHV' in radar.fields.keys():
            aux1 = np.ma.masked_where(radar.fields['RHOHV']['data'] < 0.85, radar.fields['TH']['data'] )
            aux2 = np.ma.masked_where(radar.fields['RHOHV']['data'] < 0.85, radar.fields['TV']['data'] )
            TDRc = aux1 - aux2
        else:
            TDRc = radar.fields['TH']['data'] - radar.fields['TV']['data']

        radar.add_field_like('TH', 'ZDRc', TDRc, replace_existing=True)
        radar.fields['ZDRc']['units'] = "[dB]"
        radar.fields['ZDRc']['standard_name'] = "Differential Reflectivity"
        print('ZDRc procesado y agregado!')
        return 0

    else:
        print('[ERROR]: Campo TH o TV inexistente')
        return -1

def suavizar_campo(radar, field='ZDR'):
    if field in radar.fields.keys():        
        smooth_field = radar.fields[field]['data'].copy()
        smooth_field[np.ma.where(radar.fields['RHOHV']['data']<0.8)] = np.ma.masked
        #smooth_zdr = pyart.correct.phase_proc.smooth_and_trim(smooth_zdr, 9)
        for i in range(smooth_field.shape[0]):
            smooth_field[i,:] = pyart.correct.phase_proc.smooth_and_trim(smooth_field[i,:], 9)

        #smooth_field = np.ma.masked_greater(smooth_field,10)
        radar.add_field_like(field, field+'_smooth', smooth_field, replace_existing=True)
        print('Agregado campo '+ field + '_smooth!')
        return 0
    
    else:
        print('[ERROR]: Campo ' + field+ ' inexistente')
        return -1

def calcular_kdp(radar):
    if 'PHIDP' and 'RHOHV'in radar.fields.keys():
        aux1 = np.ma.masked_where(radar.fields['RHOHV']['data'] <0.8, radar.fields['PHIDP']['data'])
        radar.add_field_like('PHIDP', 'differential_phase', aux1, replace_existing=True)
        aux2 = pyart.retrieve.kdp_vulpiani(radar)
        radar.add_field_like('PHIDP', 'KDPc', aux2[0]['data'], replace_existing=True)
        radar.fields.pop('differential_phase');
        radar.fields['KDPc']['units'] = '[°/km]'
        radar.fields['KDPc']['standard_name'] = "Specific Differential Phase"
        print('KDPc procesado y agregado!')
        return 0

    else:
        print('[ERROR] Alguno de los campos necesarios (PHIDP o RHOHV) no está disponible!')
        return -1
        
def calcular_kdp_mae(radar):
    if 'PHIDP' and 'RHOHV'in radar.fields.keys():
        aux1 = np.ma.masked_where(radar.fields['RHOHV']['data'] <0.8, radar.fields['PHIDP']['data'])
        radar.add_field_like('PHIDP', 'differential_phase', aux1, replace_existing=True)
        aux2 = pyart.retrieve.kdp_maesaka(radar)
        radar.add_field_like('PHIDP', 'KDPm', aux2[0]['data'], replace_existing=True)
        radar.fields.pop('differential_phase');
        radar.fields['KDPm']['units'] = '[°/km]'
        radar.fields['KDPm']['standard_name'] = "Specific Differential Phase"
        print('KDPm procesado y agregado!')
        return 0

    else:
        print('[ERROR] Alguno de los campos necesarios (PHIDP o RHOHV) no está disponible!')
        return -1
        
def calcular_pp_mati(radar):
    
    rho_lim = 0.94

    filtered_field = np.ma.masked_where(radar.fields['RHOHV']['data'] < rho_lim, radar.fields['DBZH']['data'] )
    linear_filtered_field = 10**(filtered_field/10)
    precip_field = (linear_filtered_field/200)**(1/1.6)
    radar.add_field_like('DBZH', 'PRECIP', precip_field, replace_existing=True)
    radar.fields['PRECIP']['units'] = 'mm/h'
    print('PP calculada')
    return 0

def calcular_pp_mati2(radar):
    ## expresion de ignacio
    rho_lim = 0.94

    filtered_field = np.ma.masked_where(radar.fields['RHOHV']['data'] < rho_lim, radar.fields['KDPc']['data'] )
    linear_filtered_field = np.abs(filtered_field)
    precip_field2 = 30.6*(linear_filtered_field)**(0.76)
    radar.add_field_like('KDPc', 'PRECIP2', precip_field2, replace_existing=True)
    radar.fields['PRECIP2']['units'] = 'mm/h'
    print('PP2 calculada')
    return 0

import numpy as np
import math
import pyart

def get_nearest_gate_azimuth2(radar, longitud, latitud, verbose=False):
    """
    Calcula el gate y el rayo más cercano de un punto geográfico respecto al radar.
    
    Parámetros
    ----------
    radar : objeto Py-ART
        Radar de Py-ART
    longitud : float
        Longitud del punto en grados decimales
    latitud : float
        Latitud del punto en grados decimales
    verbose : bool
        True para prints de debug

    Retorna
    -------
    gate : int o None
        Número de gate más cercano. None si el punto está dentro del primer gate
    alfa : int o None
        Índice del rayo más cercano. None si el punto está dentro del primer gate
    """

    # Coordenadas cartesianas relativas al radar (en metros)
    x, y = pyart.core.geographic_to_cartesian_aeqd(
        longitud, latitud,
        radar.longitude['data'][0],
        radar.latitude['data'][0]
    )
    r = math.hypot(float(x), float(y))  # distancia al radar

    # Distancia del primer gate al radar
    first_gate_x, first_gate_y = pyart.core.geographic_to_cartesian_aeqd(
        radar.gate_longitude['data'][0,0],
        radar.gate_latitude['data'][0,0],
        radar.longitude['data'][0],
        radar.latitude['data'][0]
    )
    r_first = math.hypot(float(first_gate_x), float(first_gate_y))

    # Si el punto está sobre el radar o dentro del primer gate → descartar
    if r < r_first:
        return None, None

    # Ángulo geométrico: 0° norte, sentido horario
    theta = (math.degrees(math.atan2(x, y)) + 360) % 360

    # Índice de rayo más cercano
    azimuths = radar.azimuth['data']
    alfa = int(np.argmin(np.abs(azimuths - theta)))

    # Cálculo de distancia a gates
    second_gate_x, second_gate_y = pyart.core.geographic_to_cartesian_aeqd(
        radar.gate_longitude['data'][0,1],
        radar.gate_latitude['data'][0,1],
        radar.longitude['data'][0],
        radar.latitude['data'][0]
    )
    r_second = math.hypot(float(second_gate_x), float(second_gate_y))
    dist_bet_gates = r_second - r_first

    # Número de gate más cercano
    gate = round((r - r_first) / dist_bet_gates)

    # Proteger gate dentro de límites
    ngates = radar.gate_latitude['data'].shape[1]
    gate = max(0, min(gate, ngates-1))

    if verbose:
        print('-----------------------------------------------')
        print(f'Punto a {r/1000:.3f} km del radar, ángulo {theta:.2f}°')
        print(f'Rayo más cercano (alfa): {alfa}, gate: {gate}')
        print('-----------------------------------------------')

    return gate, alfa



def get_nearest_gate_azimuth(radar, longitud, latitud, verbose=False):
    """
    Funcion para calcular el angulo donde se ubica una estación contando desde el norte
    en sentido horario, la distancia de la estación al radar (en km), el nro de gate y el azimuth del
    del gate mas cercano. Y finalmente las coordenadas geograficas (lat, lon y altitud) del
    gate mas cercano.
    Para la ejecucion de esta funcion son necesarios los paquetes PyART y Math
    
    Parameters:
              radar (radar obj): objeto radar
              longitud (float): longitud del punto de interes (en grados decimales)
              latitud (float): latitud del punto de interes (en grados decimales)
              verbose (Bool): True para obtener los print de pantalla
    
    Returns:
              gate (int): es el numero del gate mas cercano al punto
              alfa (int): es el numero de rayo correspondiente al gate mas cercano
    """
    # Calculo coordenadas x,y de la estacion
    x,y = pyart.core.geographic_to_cartesian_aeqd(longitud,
                                                  latitud,
                                                  radar.longitude['data'][0],
                                                  radar.latitude['data'][0]) 

    
    x = x.item()
    y = y.item()

    r = math.sqrt(x*x + y*y)   
    if x > 0 and y > 0: # Si el punto x,y esta en el 1er cuadrante
        alfa = round(abs(math.degrees(math.atan(x/y)))) # Angulo redondeado al entero mas cercano
        theta = abs(math.degrees(math.atan(x/y)))       # Angulo exacto
    elif x > 0 and y < 0: # Si el punto x,y esta en el 2do cuadrante
        alfa = round(abs(math.degrees(math.atan(abs(y)/x)) + 90)) # Angulo redondeado al entero mas cercano
        theta = abs(math.degrees(math.atan(abs(y)/x)) + 90)       # Angulo exacto
    elif x < 0 and y > 0: # Si el punto x,y esta en el 4to cuadrante
        alfa = round(abs(math.degrees(math.atan(y/abs(x))) + 270)) # Angulo redondeado al entero mas cercano
        theta = abs(math.degrees(math.atan(y/abs(x))) + 270)       # Angulo exacto
    elif x < 0 and y < 0: # Si el punto x,y esta en el 3er cuadrante
        alfa = round(abs(math.degrees(math.atan(x/y)) + 180)) # Angulo redondeado al entero mas cercano
        theta = abs(math.degrees(math.atan(x/y)) + 180)       # Angulo exacto

    
    
    
    # DISTANCIA AL PLUVIOMETRO EN KM. Alfa contando desde el Norte geografico en sentido horario
    r_km = r/1000 # Paso r en metros a r_km en kilometros
    
    
    
    # CALCULO DE LA DISTANCIA DEL 1ER GATE AL RADAR
    # para el calculo de la distancia al radar
    first_gate_latitude = radar.gate_latitude['data'][0, 0] # Latitud del primer gate con azimuth 0°
    first_gate_longitude = radar.gate_longitude['data'][0, 0] # Longitud del primer gate con azimuth 0°
    first_x,first_y = pyart.core.geographic_to_cartesian_aeqd(first_gate_longitude,
                                                              first_gate_latitude,
                                                              radar.longitude['data'][0],
                                                              radar.latitude['data'][0]) # Coord. x y del 
                                                                            # primer gate con
                                                                            # azimuth 0
    first_x = first_x.item()
    first_y = first_y.item()
    r_first = math.sqrt(first_x*first_x+first_y*first_y) # Distancia al primer gate

    # CALCULO DE LA DISTANCIA DEL 2DO GATE AL RADAR
    # para el calculo de la distancia al radar
    second_gate_latitude = radar.gate_latitude['data'][0, 1] # Latitud del segundo gate con azimuth 0°
    second_gate_longitude = radar.gate_longitude['data'][0, 1] # Latitud del segundo gate con azimuth 0°
    second_x,second_y = pyart.core.geographic_to_cartesian_aeqd(second_gate_longitude,
                                                                second_gate_latitude,
                                                                radar.longitude['data'][0],
                                                                radar.latitude['data'][0]) # Coord. x y del
                                                                              # segundo gate
                                                                              # con azimuth 0
    
    second_x = second_x.item()
    second_y = second_y.item()
    r_second = math.sqrt(second_x*second_x+second_y*second_y) # Distancia al segundo gate

    # Distancia entre gates (dist 2do gate<->radar - dist 1er gate<->radar )
    dist_bet_gates = r_second - r_first 

    # (dist. pluv. - dist. 1st gate) / dist. entre gates = numero de gate
    gate = round((r-r_first)/dist_bet_gates) 

    # LATITUD, LONGITUD Y ALTITUD DEL GATE MAS CERCANO AL PLUVIOMETRO
    gate_latitude = radar.gate_latitude['data'][alfa, gate]
    gate_longitude = radar.gate_longitude['data'][alfa, gate]
    gate_altitude = radar.gate_altitude['data'][alfa, gate]

    if verbose:
        print('-----------------------------------------------')
        print('Angulo donde se ubica la estacion:',theta,'°','contando desde el norte geografico')
        print('El pluviometro esta a',r_km,'km del radar')
        print(alfa,'° es el angulo redondeado')
        print ('gate más cercano:',gate)
        print('Coordenadas del centro del gate', gate,'con azimuth',alfa,':')
        print('Latidud  ','  Longitud','Altitud')
        print(gate_latitude, gate_longitude, gate_altitude)
        print('-----------------------------------------------')
    
    return gate,alfa