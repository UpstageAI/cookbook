import 'package:flutter/material.dart';
import 'package:students_ai_app/widgets/chatbot_widget.dart';
import 'package:students_ai_app/widgets/sidebar_widget.dart';

class ChatbotPage extends StatefulWidget {
  const ChatbotPage({super.key});

  @override
  State<ChatbotPage> createState() => _ChatbotPageState();
}

class _ChatbotPageState extends State<ChatbotPage> {

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // 사이드바
          SidebarWidget(),
          // 본문 영역
          Expanded(
            child: Padding(
              padding: EdgeInsets.all(12),
              child: ChatbotWidget()
            )
          )
        ],
      ),
    );
  }
}
