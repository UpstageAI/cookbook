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

        # Extract and output only URLs
        for output_item in response.output:
            if hasattr(output_item, 'content'):  # If it's a message type
                for content in output_item.content:
                    if hasattr(content, 'annotations'):  # If it has annotations
                        for annotation in content.annotations:
                            if annotation.type == 'url_citation':  # If it's a URL citation
                                urls.append(annotation.url)

        return urls