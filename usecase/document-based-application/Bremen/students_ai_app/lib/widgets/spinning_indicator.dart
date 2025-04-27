import 'dart:math' as math;
import 'package:flutter/material.dart';

class SpinningImage extends StatefulWidget {
  final String imagePath;
  final double size;
  final Duration duration;

  const SpinningImage({
    super.key,
    required this.imagePath,
    this.size = 40.0,
    this.duration = const Duration(seconds: 1),
  });

  @override
  State<SpinningImage> createState() => _SpinningImageState();
}

class _SpinningImageState extends State<SpinningImage>
  with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    )..repeat(); // 무한 회전
    super.initState();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (_, child) {
          return Transform.rotate(
            angle: _controller.value * 2 * math.pi,
            child: child,
          );
        },
        child: Image.asset(widget.imagePath),
      ),
    );
  }
}
