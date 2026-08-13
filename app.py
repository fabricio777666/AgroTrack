from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1> Sistema AgroTrack Rodando!</h1><p>A estrutura base foi criada com sucesso.</p>"

if __name__ == '__main__':
    app.run(debug=True)