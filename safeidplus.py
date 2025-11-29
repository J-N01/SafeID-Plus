#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Tuple

import webbrowser


def ensure_dependencies() -> None:
    missing_pkgs = []

    try:
        import fitz  # type: ignore  # noqa: F401
    except ImportError:
        missing_pkgs.append("pymupdf")

    try:
        from PIL import Image  # type: ignore  # noqa: F401
    except ImportError:
        missing_pkgs.append("Pillow")

    if not missing_pkgs:
        return

    print("[INFO] Faltan dependencias:")
    for pkg in missing_pkgs:
        print(f"   - {pkg}")

    ans = input("[?] ¿Querés intentar instalarlas usando pip? [s/n]: ").strip().lower()
    if ans not in ("s", "si", "sí"):
        print("\n[ERROR] No se puede continuar las conversiones sin estas librerías.")
        print("Instalalas manualmente, por ejemplo:\n")
        cmd = [sys.executable, "-m", "pip", "install"] + missing_pkgs
        print("   " + " ".join(cmd))
        sys.exit(1)

    cmd = [sys.executable, "-m", "pip", "install"] + missing_pkgs
    try:
        subprocess.check_call(cmd)
    except Exception as e:
        print(f"[ERROR] No se pudieron instalar las dependencias automáticamente: {e}")
        print("Probá instalarlas manualmente con:\n")
        print("   " + " ".join(cmd))
        sys.exit(1)

    try:
        import fitz  # type: ignore  # noqa: F401
        from PIL import Image  # type: ignore  # noqa: F401
    except ImportError as e:
        print("[ERROR] Luego de instalar, las dependencias siguen sin poder importarse.")
        print("Detalle:", e)
        sys.exit(1)


def open_folder(path: Path) -> None:
    folder = path if path.is_dir() else path.parent
    try:
        if os.name == "nt":
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception as e:
        print(f"[WARN] No se pudo abrir la carpeta {folder}: {e}")


def is_original_png_dir_name(name: str) -> bool:
    return name.endswith(" PNG´s")


def pdf_to_pngs(pdf_path: Path, dpi: int = 300) -> Path:
    import fitz  # type: ignore

    if not pdf_path.exists():
        raise FileNotFoundError(f"No existe el PDF: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"No es un PDF: {pdf_path}")

    base_stem = pdf_path.stem

    png_dir = pdf_path.parent / f"{base_stem} PNG´s"
    png_dir.mkdir(exist_ok=True)

    safeid_dir = pdf_path.parent / f"{base_stem} SafeID"
    if safeid_dir.exists():
        if safeid_dir.is_dir():
            print(f"[INFO] Carpeta para PNG protegidos ya existe: {safeid_dir}")
        else:
            print(f"[WARN] Existe un archivo llamado {safeid_dir}, no se puede crear carpeta para PNG protegidos.")
    else:
        safeid_dir.mkdir()
        print(f"[INFO] Carpeta creada para PNG protegidos: {safeid_dir}")

    print(f"[INFO] Convirtiendo PDF -> PNG(s): {pdf_path}")
    doc = fitz.open(pdf_path)
    try:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=dpi)
            out_name = f"{base_stem}_page{i:02d}.png"
            out_path = png_dir / out_name
            pix.save(str(out_path))
            print(f"   - Generado: {out_path}")
    finally:
        doc.close()

    print(f"[OK] PNG(s) para {pdf_path.name} en: {png_dir}")
    print(f"[INFO] Guardá los PNG protegidos de Safe ID en: {safeid_dir}")
    return png_dir


def cmd_pre(inputs: List[str], dpi: int) -> None:
    processed_dirs: List[Path] = []

    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_file() and path.suffix.lower() == ".pdf":
            out_dir = pdf_to_pngs(path, dpi=dpi)
            processed_dirs.append(out_dir)
        elif path.is_dir():
            pdfs = sorted(path.glob("*.pdf"))
            if not pdfs:
                print(f"[WARN] No se encontraron PDFs en carpeta: {path}")
                continue
            for pdf in pdfs:
                out_dir = pdf_to_pngs(pdf, dpi=dpi)
                processed_dirs.append(out_dir)
        else:
            print(f"[WARN] Entrada ignorada (no es PDF ni carpeta): {path}")

    if not processed_dirs:
        print("[ERROR] No se procesó ningún PDF.")
        sys.exit(1)

    if len(processed_dirs) == 1:
        out_dir = processed_dirs[0]
        print(f"[INFO] Abriendo carpeta de PNG originales: {out_dir}")
        open_folder(out_dir)
        print("[INFO] Abriendo Safe ID en el navegador...")
        webbrowser.open("https://safeid.datosargentinos.com/")

    print("\n[INFO] Flujo sugerido:")
    print("  - PNG originales en `NombreDelPdf PNG´s/`.")
    print("  - Cargá los PNG originales en la herramienta `SafeID/`.")
    print("  - PNG protegidos en `NombreDelPdf SafeID/`.")
    print("  - Luego ejecutá `safeidplus.py post` sobre la carpeta SafeID (donde guardaras los png's protegidos).\n")


def images_to_pdf(images: List[Path], output_pdf: Path) -> None:
    from PIL import Image  # type: ignore

    if not images:
        raise ValueError("La lista de imágenes está vacía.")

    images = [p for p in images if p.exists()]
    if not images:
        raise ValueError("Las imágenes indicadas no existen.")

    print("[INFO] Imágenes a combinar en PDF (en este orden):")
    for img in images:
        print(f"   - {img}")

    pil_images = []
    for p in images:
        img = Image.open(p)
        if img.mode != "RGB":
            img = img.convert("RGB")
        pil_images.append(img)

    first = pil_images[0]
    rest = pil_images[1:]

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    first.save(str(output_pdf), save_all=True, append_images=rest)
    print(f"[OK] PDF protegido creado: {output_pdf}")


def parse_folder_base_and_keyword(folder_name: str) -> Tuple[str, str]:
    if folder_name.endswith(" SafeID"):
        return folder_name[:-len(" SafeID")], ""

    suffix = "_protegido"
    if folder_name.endswith(suffix):
        head = folder_name[:-len(suffix)]
        if "_" in head:
            base, kw = head.rsplit("_", 1)
            return base, kw
        else:
            return head, ""
    else:
        return folder_name, ""


def image_sort_key(path: Path):
    name = path.name

    m = re.match(r'^(.*?)(?: \((\d+)\))?(\.[^.]+)$', name)
    if m:
        base = m.group(1)
        num = m.group(2)
        idx = int(num) if num is not None else 0
        return (base.lower(), idx)

    digits = re.findall(r'\d+', name)
    idx = int(digits[0]) if digits else 0
    base = re.sub(r'\d+', '', name)
    return (base.lower(), idx, name.lower())


def process_png_protegido_folder(folder: Path) -> None:
    from PIL import Image  # type: ignore

    if not folder.is_dir():
        print(f"[WARN] No es carpeta: {folder}")
        return

    base, current_kw = parse_folder_base_and_keyword(folder.name)

    if current_kw:
        prompt = (
            f"[?] Palabra clave para versión protegida de '{base}' "
            f"(Enter para dejar '{current_kw}'): "
        )
    else:
        prompt = (
            f"[?] Palabra clave para versión protegida de '{base}' "
            f"(ej: banco, afip; Enter para sin clave): "
        )

    user_kw = input(prompt).strip()
    if user_kw == "":
        final_kw = current_kw
    else:
        final_kw = user_kw

    if final_kw:
        common = f"{base}_{final_kw}_protegido"
    else:
        common = f"{base}_protegido"

    images = (
        list(folder.glob("*.png")) +
        list(folder.glob("*.jpg")) +
        list(folder.glob("*.jpeg"))
    )
    if not images:
        print(f"[WARN] Sin imágenes PNG/JPG en: {folder}")
        return

    images.sort(key=image_sort_key)

    print("[INFO] Normalizando nombres y formato de imágenes protegidas...")
    new_images: List[Path] = []
    for idx, old_path in enumerate(images, start=1):
        page_str = f"{idx:02d}"
        new_name = f"{common}_page{page_str}.png"
        new_path = folder / new_name

        if old_path == new_path and old_path.suffix.lower() == ".png":
            new_images.append(new_path)
            continue

        try:
            img = Image.open(old_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(str(new_path), "PNG")
            print(f"   - {old_path.name} -> {new_name}")
        except Exception as e:
            print(f"[WARN] No se pudo procesar la imagen {old_path}: {e}")
            continue

        if old_path != new_path:
            try:
                old_path.unlink()
            except OSError as e:
                print(f"[WARN] No se pudo eliminar el archivo viejo {old_path}: {e}")

        new_images.append(new_path)

    if not new_images:
        print(f"[ERROR] No quedaron imágenes válidas para generar el PDF en {folder}")
        return

    out_pdf = folder / f"{common}.pdf"
    images_to_pdf(new_images, out_pdf)


def cmd_post(inputs: List[str]) -> None:
    any_processed = False

    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            print(f"[WARN] Ruta inexistente: {path}")
            continue

        if path.is_dir():
            if not is_original_png_dir_name(path.name):
                imgs_here = (
                    list(path.glob("*.png")) +
                    list(path.glob("*.jpg")) +
                    list(path.glob("*.jpeg"))
                )
                if imgs_here:
                    process_png_protegido_folder(path)
                    any_processed = True

            for folder in sorted(
                p for p in path.iterdir()
                if p.is_dir() and not is_original_png_dir_name(p.name)
            ):
                imgs_sub = (
                    list(folder.glob("*.png")) +
                    list(folder.glob("*.jpg")) +
                    list(folder.glob("*.jpeg"))
                )
                if imgs_sub:
                    process_png_protegido_folder(folder)
                    any_processed = True

        else:
            print(f"[WARN] Entrada ignorada (no es carpeta): {path}")

    if not any_processed:
        print("[ERROR] No se generó ningún PDF protegido. Verificá las rutas y nombres.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automatiza PDF->PNG y PNG protegido->PDF para Safe ID."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    pre_parser = subparsers.add_parser(
        "pre",
        help="Convertir PDF(s) a PNG(s) en `NombreDelPdf PNG´s/` y crear `NombreDelPdf SafeID/`."
    )
    pre_parser.add_argument(
        "inputs",
        nargs="+",
        help="Uno o más PDFs o carpetas que contengan PDFs."
    )
    pre_parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolución en DPI para la conversión PDF->PNG (por defecto 300)."
    )

    post_parser = subparsers.add_parser(
        "post",
        help="Renombrar PNGs protegidos y generar PDFs en la misma carpeta."
    )
    post_parser.add_argument(
        "inputs",
        nargs="+",
        help="Carpetas con PNGs protegidos."
    )

    args = parser.parse_args()

    if args.command == "pre":
        cmd_pre(args.inputs, dpi=args.dpi)
    elif args.command == "post":
        cmd_post(args.inputs)
    else:
        parser.print_help()


if __name__ == "__main__":
    ensure_dependencies()
    main()
