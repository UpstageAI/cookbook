# 로그 파일 준비
sudo touch /var/log/hackathon_app.log
sudo chmod 666 /var/log/hackathon_app.log

# Poetry 환경 설정
poetry env use "$(pyenv which python)"
poetry install --no-root

# PYTHONPATH 설정 후 nohup으로 Streamlit 실행
export PYTHONPATH=$PWD/src
nohup poetry run streamlit run src/housing_alert/streamlit_app.py \
  --server.port 8501 > /var/log/hackathon_app.log 2>&1 &