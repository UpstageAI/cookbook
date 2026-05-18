"""
서비스 설명 기재 (최초로 진입하는 페이지)
"""

import streamlit as st

st.title("💭 UpThink")
st.caption("""Think + Upstage ✨\\
지식을 정리하는 사고에만 몰입해 보세요!""")

st.markdown(
    """### 개요
개인 지식 관리 환경(Obsidian)에서 노트에 지식을 정리할 때, 가장 중요한 사고의 흐름이 끊긴 적 있으신가요?

▪︎ㅤ노트 내 이미지의 정보를 직접 옮겨 적거나 \\
▪︎ㅤ태그의 대소문자나 구분자 등 스타일링 규칙을 고민하거나 \\
▪︎ㅤ작성 중인 내용과 연관된 과거 노트를 찾기 위해 탐색하거나 \\
▪︎ㅤ내용이 너무 많아진 노트를 어떻게 분할할지 막막하거나

UpThink는 Upstage Solar Pro 2의 강력한 언어 이해 능력을 활용하여 이러한 지식 관리의 병목 구간을 해결합니다. \\
이미지 분석부터 태그 정리, 연관 지식 탐색, 노트 분할까지! 번거로운 정리 작업은 AI에게 맡기고, 가장 중요한 사고 활동에만 몰입해 보세요.
"""
)

st.divider()

st.markdown("### 시연 영상")
st.markdown("👇 사용 방법은 시연 영상을 참고해 주세요!")
st.video("https://www.youtube.com/watch?v=8bjLew7KTW4", width=900)

st.divider()

st.markdown("### 주요 서비스 기능")
st.markdown(
    """##### 1️⃣ 이미지 대체 텍스트 생성
노트 내 이미지를 탐색하여 Upstage Document Parse로 텍스트를 추출한 후, Solar Pro 2를 사용하여 이미지를 설명하는 대체 텍스트를 생성합니다. \\
생성된 대체 텍스트는 `(대체 텍스트 by Upstage)` 코드 블록으로 이미지 링크 아래에 추가되어, 수정된 Markdown 파일을 다운로드할 수 있습니다."""
)
st.image(
    "https://github-production-user-asset-6210df.s3.amazonaws.com/171089104/527155856-9d7a9c48-0e53-45f3-88d9-1cb0c6ea3981.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20251216%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251216T163232Z&X-Amz-Expires=300&X-Amz-Signature=a295d1d084ff3ae49e59d83cacb69588851300012ae4a143711a8e4116d72fb1&X-Amz-SignedHeaders=host",
    width=800,
)
st.markdown(
    """##### 2️⃣ 태그 추천
Obsidian Vault 경로에 있는 모든 Markdown 파일에서 2가지 태그 패턴을 추출합니다. \\
사용자가 업로드한 파일 내용과 직접 설정한 가이드라인(언어, 포맷 등)을 기반으로 태그를 생성하고, 기존 태그와의 유사도를 비교해 최종 태그를 선별합니다. \\
최종 선정된 태그 목록은 YAML Frontmatter 형식으로 노트 최상단에 자동으로 추가되어, 사용자가 수정된 Markdown 파일을 다운로드할 수 있습니다."""
)
st.image(
    "https://github-production-user-asset-6210df.s3.amazonaws.com/171089104/527155896-4b950ff7-6a1b-4df9-ac76-afc5f1defac9.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20251216%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251216T163318Z&X-Amz-Expires=300&X-Amz-Signature=24911f26b551015c43a0503775a4281b4d3b5468912e2ec1076b209a82bf900e&X-Amz-SignedHeaders=host",
    width=800,
)
st.markdown(
    """##### 3️⃣ 연관 노트 추천
Vault 내 노트를 Upstage Embedding Model로 벡터화하여 Chroma DB에 저장합니다. \\
업로드한 노트와 유사도가 높은 Top 3 노트를 검색하여 추천합니다. \\
추천된 노트는 `## Related Notes` 섹션에 백링크 형식으로 자동 삽입됩니다."""
)
st.image(
    "https://github-production-user-asset-6210df.s3.amazonaws.com/171089104/527155923-1ee795f1-9bcc-4916-9bbc-190dff0ee82e.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20251216%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251216T163334Z&X-Amz-Expires=300&X-Amz-Signature=5ac8983cf767cf81996427e2e5046d481fa04d2bde1d5ec5ba3a4fca7baeae02&X-Amz-SignedHeaders=host",
    width=800,
)
st.markdown(
    """##### 4️⃣ 노트 분할
Solar Pro 2로 노트에서 주제(Topic)를 자동 추출하고, 사용자가 편집/삭제/추가할 수 있습니다. \\
각 주제별로 원자 노트를 생성하여 지정된 폴더에 저장합니다. \\
원본 노트에는 백링크와 `## Generated Atomic Notes` 섹션이 자동으로 추가됩니다."""
)
st.image(
    "https://github-production-user-asset-6210df.s3.amazonaws.com/171089104/527155946-f834e4a6-7227-4dcd-81e3-5087cf5f218c.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20251216%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251216T163350Z&X-Amz-Expires=300&X-Amz-Signature=34e0ed69aa99677f81b7cef22958ef47cd54d01c434ea000cf7e2d9aef2c626a&X-Amz-SignedHeaders=host",
    width=800,
)

st.divider()

st.markdown("""**Acknowledgements** \\
이 프로젝트는 **Upstage AI Ambassador** 활동의 일환으로 진행되었습니다. \\
프로젝트를 진행할 수 있도록 Credit을 지원해 주신 **[Upstage](https://www.upstage.ai/)** 에 감사드립니다.""")