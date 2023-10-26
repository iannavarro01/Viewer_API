# run.py
import os
from app import create_app

app = create_app()

# Inicie o agendador de limpeza da tabela 2fa

if __name__ == '__main__':
    app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 5002)),
            debug=False)  # Se for usada em testes ainda, utilizar (debug=true)
