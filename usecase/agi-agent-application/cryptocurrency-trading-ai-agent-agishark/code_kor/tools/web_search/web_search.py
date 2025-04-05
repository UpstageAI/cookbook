from openai import OpenAI

class WebSearchTool:
    def __init__(self):
        self.client = OpenAI()

    def __call__(self, search_query):
        response = self.client.responses.create(
    model="gpt-4o",
    tools=[{"type": "web_search_preview"}],
    input=search_query
)
        urls = []

        # URL만 추출해서 출력
        for output_item in response.output:
            if hasattr(output_item, 'content'):  # 메시지 타입인 경우
                for content in output_item.content:
                    if hasattr(content, 'annotations'):  # 어노테이션이 있는 경우
                        for annotation in content.annotations:
                            if annotation.type == 'url_citation':  # URL 인용인 경우
                                urls.append(annotation.url)

        return urls