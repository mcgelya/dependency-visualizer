from fastapi import FastAPI, Request, File, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyvis.network import Network
from typing import List
import networkx as nx
import matplotlib.cm as cm
import matplotlib.colors as mcolors

import dep_graph
import uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


async def generate_graph_html(G: nx.DiGraph) -> str:
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#000000", directed=True)
    root = 'Your project'
    distances = nx.single_source_shortest_path_length(G, root)
    max_distance = max(distances.values())

    def compute_size(dist):
        max_size = 30
        min_size = 10
        scale = (max_size - min_size) / max(1, max_distance)
        return max_size - dist * scale

    cmap = cm.get_cmap("Pastel2")
    norm = mcolors.Normalize(vmin=0, vmax=max_distance)

    def compute_color(dist):
        return mcolors.to_hex(cmap(norm(dist)))

    for node, attributes in G.nodes(data=True):
        color = compute_color(distances[node])
        size = compute_size(distances[node])
        net.add_node(
            node,
            label=node,
            title=f"{attributes.get('version', 'N/A')}",
            color=color,
            size=size
        )

    for edge in G.edges():
        net.add_edge(edge[0], edge[1], color="#005f99", width=1)

    return net.generate_html()


@app.get("/", response_class=HTMLResponse)
async def main(request: Request, message: str = None):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Dependency Visualizer", "message": message}
    )


graphs = dict()
compiler = dep_graph.DependencyCompiler()


def generate_dep_graph(requirements: List[str], token: str):
    try:
        result = compiler.generate_graph(requirements)
        graphs[token] = (result, None)
    except Exception as e:
        graphs[token] = (None, str(e))


@app.get("/graph/{token}")
async def show_graph(request: Request, token: str):
    if token in graphs:
        G, err = graphs[token]
        if G is not None:
            graph_html = await generate_graph_html(G)
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "graph_html": graph_html}
            )
        else:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "title": "Dependency Visualizer", "error_message": f'{err}'}
            )
    else:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "title": "Dependency Visualizer",
             "message": "Graph is being generated. Please keep refreshing page..."}
        )


@app.post("/upload/")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    token = uuid.uuid4().hex

    try:
        requirements = await file.read()
        requirements_list = requirements.decode('utf-8').splitlines()
        background_tasks.add_task(generate_dep_graph, requirements_list, token)

        return RedirectResponse(url=f'/graph/{token}', status_code=303)
    except:
        return RedirectResponse(url=f'/', status_code=303)
