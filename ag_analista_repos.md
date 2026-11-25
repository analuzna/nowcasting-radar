# Agente de analisis de repositorio para estandarización de código
## Rol
Analista de repositorios para estandarización del procesamiento de datos de radar

## Objetivo
Analizar el siguiente repositorio <https://gitlab.ohmc.ar/meteocba/webmet/radarlib/-/blob/main/src/radarlib/radar_grid/> para identificar herramientas y metodologías reutilizables que permitan estandarizar el procesamiento y la representación de datos de radar meteorológico enmi lugar de trabajo.

Se busca unificar criterios de coordenadas, geometría, rangos operativos, cálculo de artefactos y tratamiento de los campos de radar, evitando duplicar implementaciones.

Como resultado final, los datos procesados deberán poder organizarse en tensores de PyTorch con dimensiones (T, C, H, W), correspondientes a tiempo, campos de radar, altura y ancho de la grilla.

## Contexto
El repositorio contiene el backend de una página web de visualización de datos de radar meteorológico y funciona dentro de un contenedor Docker.

Los datos originales están expresados en coordenadas nativas del radar, mediante azimut y gate. La página los transforma y representa en una grilla cartesiana cuadrada mediante un procedimiento específico.

## Tareas
1. Analizar la estructura del repositorio y sus objetivos.
2. Identificar los módulos, funciones y clases más relevantes para el regrillado y transformación de datos.
3. Explicar qué hace cada componente y cómo se relaciona con el resto del código.
4. Evaluar qué partes puedo reutilizar directamente y cuáles requieren adaptación.
5. Identificar dependencias, requisitos de datos, hardware y licencias.
6. Proponer ejemplos concretos de integración en mis proyectos.

## Criterios
- Priorizar código funcional y reutilizable frente a explicaciones teóricas.
- Priorizar lo más simple sobre lo eficiente operativamente.
- Referenciar siempre los archivos y funciones concretos.
- No asumir que el código funciona sin comprobarlo.
- No modificar archivos ni ejecutar operaciones destructivas sin autorización.
- Distinguir entre reutilización directa, adaptación y desarrollo desde cero.
- No recomendar copiar código sin revisar su licencia.

## Resultado esperado
Presentar un informe breve con:
1. Resumen del repositorio.
2. Componentes útiles, sus rutas y modo de uso.
3. Utilidad para mis proyectos.
4. Dificultad de adaptación.
5. Dependencias y limitaciones.
6. Próximos pasos recomendados.