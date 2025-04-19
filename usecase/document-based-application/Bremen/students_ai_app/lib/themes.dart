import 'package:flutter/material.dart';

const Color primaryColor = Color (0xFFADBBFE);
const Color primaryColorDark = Color (0xFF815EFA);

class AppTheme {
  static ThemeData lightTheme(BuildContext context) {
    return ThemeData(
      fontFamily: "KdamThmorPro",
      colorSchemeSeed: Colors.white,
      canvasColor: Colors.white,
      dividerColor: Colors.white,
      hintColor: Colors.white,
      hoverColor: Colors.white,
      indicatorColor: Colors.white,
      scaffoldBackgroundColor: Colors.white,
      secondaryHeaderColor: Colors.white,
      unselectedWidgetColor: Colors.white, dialogTheme: DialogThemeData(backgroundColor: Colors.white),
    );
  }
}

const Color textBlackColor = Color(0xFF1B1B1B);
const Color textGrayColor = Color(0xFF707070);
const Color textWhiteColor = Color(0xFFF5F5F7);
const Color boxGrayColor = Color(0xFFF5F5F7);
const Color boxBlueColor = Color(0xFFE4EBF5);
const Color buttonGrayColor = Color(0xFFF5F5F7);
const Color dividerNormal = Color(0xFFC7C7C7);
const Color dividerStrong = Color(0xFF8D8D8D);
const Color warningColor = Color(0xFFFA8219);
const Color errorColor = Color(0xFFE60000);

const double defaultPadding = 16.0;
const double defaultBorderRadius = 12.0;
const Duration defaultDuration = Duration(milliseconds: 300);
const double defaultElevation = 6.0;

const FontWeight boldKdam = FontWeight.w900;
const FontWeight semiboldKdam = FontWeight.w600;
const FontWeight regularKdam = FontWeight.w300;
