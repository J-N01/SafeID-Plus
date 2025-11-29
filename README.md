# SafeID-Plus
Script para automatizar parte del proceso de uso de la herramienta [Safe ID](https://safeid.datosargentinos.com/):

- Convierte PDFs a PNGs para subir a Safe ID.
- Crea automáticamente carpetas para:
  - Los PNG originales.
  - Los PNG protegidos (descargados desde Safe ID).
- Renombra los PNG protegidos con una convención establecida.
- Reconstruye un PDF protegido a partir de esos PNG protegidos.

---

## Requisitos

- Python 3.8 o superior.
- Acceso a `pip` para instalar dependencias.
- Librerías de Python:
  - [`pymupdf`](https://pypi.org/project/PyMuPDF/)
  - [`Pillow`](https://pypi.org/project/Pillow/)

El script verifica si estas librerías están instaladas.  
Si falta alguna, te pregunta si querés instalarlas automáticamente con `pip`.

---

## Instalación

1. Guardar el archivo como `safeidplus.py` en una carpeta a elección.
2. La primera vez que se ejecuta el script, si faltan dependencias, elegir `s` para instalarlas.
---

## Flujo de trabajo

### 1. Convertir PDF a PNG's (modo `pre`)

Convierte uno o varios PDFs en PNGs (una imagen por página) y crea también la carpeta donde se guardaran los PNG protegidos de Safe ID.

Por cada PDF se crean:

- Carpeta con PNG originales:
  - `NombreDelPdf PNG´s/`
  - Contiene archivos:
    - `NombreDelPdf_page01.png`
    - `NombreDelPdf_page02.png`
    - etc.
- Carpeta para PNG protegidos:
  - `NombreDelPdf SafeID/`  
    (vacía al principio, es donde se guardaran los pngs protegidos que se descarguen de Safe ID)

#### Uso

- Uno o varios PDF's:

  ```bash
  python safeidplus.py pre "C:\Ruta\Al\PDF"
  ```

El script:

- Genera los PNG en la carpeta `NombreDelPdf PNG´s/`.
- Crea la carpeta `NombreDelPdf SafeID/`.
- Si solo había un PDF, abre la carpeta de PNG originales y el sitio de Safe ID en el navegador.

#### Qué hacer después

1. Entrar a la carpeta `NombreDelPdf PNG´s/`.
2. Subir cada PNG a Safe ID y generar las versiones protegidas (con marca de agua, blur, etc.).
3. Descargar esos PNG protegidos y guardarlos dentro de `NombreDelPdf SafeID/`.

---

### 2. Reconstruir PDF desde PNG protegidos (modo `post`)

#### Uso

  ```bash
  python safeidplus.py post "C:\Ruta\A\La\Carpeta\NombreDelPdf SafeID"
  ```
#Durante la ejecución, para cada carpeta:

1. El script infiere los nombres en base al `NombreDelPdf`.
2. Te pregunta una palabra clave (podés dejarla vacía), es algo que se elige por cada carpeta (ej.: `banco`, `arca`, `clienteX`).
3. Renombra y normaliza todos los PNG a:
   - `NombreDelPdf[_PalabraClave]_protegido_pageXX.png`
4. Genera el PDF:
   - `NombreDelPdf[_PalabraClave]_protegido.pdf`  
   en la misma carpeta.

Si no ponés nada, usa solo `NombreDelPdf_protegido...`.

#### Funcionamiento

Toma carpetas con PNG protegidos, renombra esos PNG con una convención ya establecida y genera un único PDF protegido.

Dentro de cada carpeta procesada termina habiendo:

- PNG protegidos renombrados como:
  - `NombreDelPdf[_PalabraClave]_protegido_page01.png`
  - `NombreDelPdf[_PalabraClave]_protegido_page02.png`
  - etc.
- PDF protegido:
  - `NombreDelPdf[_PalabraClave]_protegido.pdf`

#### Detección de “NombreDelPdf”

Reglas para obtener `NombreDelPdf` a partir del nombre de la carpeta:

- Si la carpeta se llama `NombreDelPdf SafeID` → Base = `NombreDelPdf`
- Si la carpeta se llama `Algo_protegido` o `Algo_clave_protegido`:
  - `Algo_protegido` → Base=`Algo`, keyword vacía.
  - `Algo_clave_protegido` → Base=`Algo`, keyword=`clave`.
- En cualquier otro caso → Base = nombre completo de la carpeta.

#### Orden de las páginas

El orden de páginas se calcula con un “orden natural” de nombres tipo:

- `foto.png`
- `foto (1).png`
- `foto (2).png`
- `foto (3).png`

No importa cómo los nombre el navegador al descargar; el script los ordena de forma lógica antes de renombrar y armar el PDF.

---

## Notas

- Funciona en Windows, macOS y Linux, siempre que tengan Python y `pip`.
- Podés tener múltiples versiones protegidas del mismo PDF (distintas marcas de agua) usando distintas carpetas y/o distintas palabras clave.
- Los PDFs originales y los PNG originales (`NombreDelPdf PNG´s/`) no se modifican.


## "Este script fue diseñado para la siguiente herramienta: https://github.com/Xyborg/datosargentinos.com"
