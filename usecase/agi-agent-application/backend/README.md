<br/>
<br/>

<p align="center">
<img src="https://files.cloudtype.io/logo/cloudtype-logo-horizontal-black.png" width="50%" alt="Cloudtype"/>
</p>

<br/>
<br/>

# Flask

Python으로 구현된 Flask 어플리케이션 템플릿입니다.

## 🖇️ 준비 및 확인사항

### 지원 Python 버전
- 3.7, 3.8, 3.9, 3.10, 3.11
- Flask는 최소 3.7 버전의 Python를 필요로 합니다.
- ⚠️ 로컬/테스트 환경과 클라우드타입에서 설정한 Python 버전이 상이한 경우 정상적으로 빌드되지 않을 수 있습니다.

### 패키지 명세
- 빌드 시 어플리케이션에 사용된 패키지를 설치하기 위해서는 `requirements.txt` 파일이 반드시 필요합니다.

## ⌨️ 명령어

### Start

```bash
gunicorn -b 0.0.0.0:5000 app:app
```

- `flask --app [app 모듈명] run` 은 개발 서버 실행 명령어이므로 사용을 지양합니다.


## 🏷️ 환경변수

- `FLASK_ENV`: 배포 환경 설정


## 💬 문제해결

- [클라우드타입 Docs](https://docs.cloudtype.io/)

- [클라우드타입 FAQ](https://help.cloudtype.io/guide/faq)

- [Discord](https://discord.gg/U7HX4BA6hu)


## 📄 License

[BSD 3-Clause](https://github.com/pallets/flask/blob/main/LICENSE.rst)

