# Use uma imagem base de Python mínima
FROM python:3.10-slim

# Instale dependências do sistema para pacotes Python
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    cmake \
    libboost-python1.67-dev \
    libboost-system1.67-dev \
    && apt-get clean \
    && pip install --upgrade pip

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie apenas os arquivos necessários
COPY requirements.txt /app/requirements.txt

# Instale dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos os arquivos para o diretório de trabalho
COPY . /app

# Exponha a porta que a aplicação vai rodar
EXPOSE 5000

# Defina variáveis de ambiente
ENV FLASK_APP=app.py

# Comando para rodar quando o container inicia
CMD ["flask", "run", "--host=0.0.0.0"]