<!-- 
<window>
    <headerBar></headerBar>
    <box main body>
        <paned>
            <stack> 
                <TerminalBox></TerminalBox>
                <StatusBar></StatusBar>
            </stack> 
            <paned>
                <chatbot></chatbot>
                <anyutil></anyutil>
                <StatusBar></StatusBar>
            </paned>  
        </paned>        
    </box main body>
</window> -->

---proyecto
----assets
----src
------components
--------right_container.py
--------terminal_box.py
--------status_bar.py
-----window.py
----README.md
----requirements.txt
----main.py

<box main body>
        <paned>
            <pack1>
                <TerminalBox></TerminalBox>
            </pack1>
            <pack2>
            <stack>
                <chatbot></chatbot>
                <anyutil></anyutil>
            </stack>  
            </pack2>
        </paned>    
        <activityBar right>    
            <icon chatbot>
            </icon>
            <icon anyutil>
            </icon>
        </activityBar>    
</box main body>

colores de canaima

#0b6793
#191919
#ececec

## dump from requirements.txt (old and bad used dont repeat)


dependencias:
pygobject
openai (sdk compatible con openrouter) 
    - vas a necesitar una api_key de openrouter es muy facil de configurar
    - visita este sitio web "https://openrouter.ai"
    - dale en get API key y sigue los pasos
    - en el panel del chatbot le das al bton superior y en el entry "api-key" pones la api que te dio open router
    - no la pierdas ya que no existe forma de recuperarla 
    - en caso de perder la api key simplemente borra la que perdiste y crea una nueva
python-dotenv [removido]
ollama
    - para ollama instalas ollama en el computador 
    - usando: curl -fsSL https://ollama.com/install.sh | sh
    - y luego ollama run <model> para instalar el modelo que gustes y que puedas correr claro esta
    - entre los modelos estan estos:
    - NAME                ID              SIZE    
    phi3.5:latest       61819fb370a3    2.2 GB
    qwen2.5:1.5b        65ec06548149    986 MB
    smollm:1.7b         95f6557a0f0f    990 MB
    tinyllama:latest    2644915ede35    637 MB
    qwen2.5:0.5b        a8b0c5157701    397 MB
    smollm:360m         b3ba1ccba2b8    229 MB
    smollm:135m         b0b2a4617438    91 MB 
    llama3.2:1b         baf6a787fdff    1.3 GB
    llama3.2:latest     a80c4f17acd5    2.0 GB
    - recomiendo llama3.2:1b si el equipo tiene 8gb ram

si estas en wsl y algo no te funciona bien es posible que tengas
que reemplazar el contenido del archivo zshrc por el que esta en este projecto

los pasos serian:
- abres la terminal en wsl
- asegurate de estar en /~ con el comando cd ~
- luego abre nano .zshrc
- reemplaza el contenido con el del fichero zshrc 
- que esta en la raiz de este proyecto

0. 
usa debian por si acaso, por defecto wsl viene con ubuntu, pero si puedes cambiar a debian mejor

1.
"""
wsl --update
wsl --shutdown
"""
2. 
"""
wsl -l -v
"""

3.
"""
sudo apt update

sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-vte-2.91 libgtk-3-dev libvte-2.91-dev
"""

4.
en la carpeta donde tengas el ejecutable
./main

para hacer un paquete o un ejecutable mejor dicho usamos el comando

pyinstaller --onefile \
--add-data "assets:assets" \
--collect-all gi \
--collect-submodules gi \
main.py

## end of dump