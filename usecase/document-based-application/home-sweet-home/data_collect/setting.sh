sudo yum update -y
sudo yum install -y wget unzip python3-pip

wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum install ./google-chrome-stable_current_x86_64.rpm -y
sudo ln -s /usr/bin/google-chrome-stable /usr/bin/google-chrome
google-chrome --version


# 크롬 최신 버전 다운로드 및 설치
wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/135.0.7049.84/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver
chromedriver --version


pip3 install selenium --user