import 'package:flutter/material.dart';
import 'package:students_ai_app/pages/chatbot_page.dart';
import 'package:students_ai_app/pages/pdf_view_page.dart';
import 'package:students_ai_app/themes.dart';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Upstage Paper Assistant',
      theme: AppTheme.lightTheme(context),
      home: ChatbotPage(),
    );
  }
}

