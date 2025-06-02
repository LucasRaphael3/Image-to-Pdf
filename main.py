from fastapi import FastAPI, UploadFile, File, Request, Form, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from uuid import uuid4
from PIL import Image
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/converter")
async def converter_imagens_para_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    nome_pdf: str = Form(...)
):
    imagens_convertidas = []
    temp_paths = []

    if not nome_pdf.lower().endswith(".pdf"):
        nome_pdf += ".pdf"

    # Ordenar arquivos por nome original
    files.sort(key=lambda x: x.filename)

    for file in files:
        if not file.content_type.startswith("image/"):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "mensagem": "Todos os arquivos devem ser imagens."
            })

        temp_img = f"temp_{uuid4()}.jpg"
        temp_paths.append(temp_img)

        with open(temp_img, "wb") as f:
            f.write(await file.read())

        img = Image.open(temp_img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        imagens_convertidas.append(img)

    if not imagens_convertidas:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "mensagem": "Nenhuma imagem válida foi enviada."
        })

    pdf_path = f"temp_{uuid4()}.pdf"
    imagens_convertidas[0].save(pdf_path, save_all=True, append_images=imagens_convertidas[1:])

    # Agendar limpeza
    for path in temp_paths:
        background_tasks.add_task(os.remove, path)
    background_tasks.add_task(os.remove, pdf_path)

    return FileResponse(pdf_path, filename=nome_pdf, media_type="application/pdf")
