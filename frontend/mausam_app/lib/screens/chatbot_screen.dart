import 'dart:ui';

import 'package:flutter/material.dart';

import '../widgets/mascot_entry_point.dart';

class ChatbotScreen extends StatefulWidget {
  const ChatbotScreen({super.key});

  @override
  State<ChatbotScreen> createState() => _ChatbotScreenState();
}

class _ChatbotScreenState extends State<ChatbotScreen>
    with SingleTickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isTyping = false;
  late final AnimationController _mascotController;

  final List<_ChatMessage> _messages = [
    const _ChatMessage(
      text: "Hi, I'm Mausam ☁️\nAsk me anything about weather, air quality, UV, rain, maps, or weather concepts.",
      isUser: false,
    ),
  ];

  @override
  void initState() {
    super.initState();

    _mascotController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2800),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _mascotController.dispose();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _isTyping) return;

    FocusScope.of(context).unfocus();

    setState(() {
      _messages.add(_ChatMessage(text: text, isUser: true));
      _messages.add(const _ChatMessage(text: '', isUser: false));
      _isTyping = true;
    });

    _controller.clear();
    _scrollToBottom();

    final response = _mockResponse(text);

    for (var i = 0; i < response.length; i++) {
      if (!mounted) return;

      await Future.delayed(const Duration(milliseconds: 28));

      if (!mounted) return;

      setState(() {
        _messages[_messages.length - 1] = _ChatMessage(
          text: response.substring(0, i + 1),
          isUser: false,
        );
      });

      _scrollToBottom();
    }

    if (mounted) {
      setState(() => _isTyping = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 120),
          curve: Curves.easeOut,
        );
      }
    });
  }

  String _mockResponse(String question) {
    final q = question.toLowerCase();

    if (q.contains('aqi') || q.contains('air quality')) {
      return 'AQI tells you how clean or polluted the air is. Lower values generally mean better air quality.';
    }

    if (q.contains('uv')) {
      return 'The UV Index measures the strength of ultraviolet radiation from the sun. Higher values mean greater sun exposure risk.';
    }

    if (q.contains('humidity')) {
      return 'Humidity is the amount of water vapour in the air. High humidity can make warm weather feel hotter.';
    }

    if (q.contains('rain')) {
      return 'I can help you understand rain chances, precipitation, and what the forecast means.';
    }

    if (q.contains('pm2.5')) {
      return 'PM2.5 refers to very small airborne particles that can enter deep into the respiratory system.';
    }

    return 'I’m Mausam ☁️. I can help with weather, air quality, UV, rain, maps, and weather concepts. Once my weather service is connected, I’ll also be able to answer using your current Mausam data.';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF081522),
      body: Stack(
        children: [
          const _AtmosphericBackground(),
          SafeArea(
            child: Column(
              children: [
                _buildHeader(),
                const SizedBox(height: 8),
                _buildMascot(),
                const SizedBox(height: 4),
                Expanded(
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(18, 8, 18, 18),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final message = _messages[index];
                      return _ChatBubble(message: message);
                    },
                  ),
                ),
                _buildInput(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 10, 18, 12),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(
              Icons.arrow_back_ios_new_rounded,
              color: Colors.white,
              size: 20,
            ),
          ),
          const SizedBox(width: 4),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Mausam',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Your weather companion',
                  style: TextStyle(color: Colors.white60, fontSize: 11),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMascot() {
    return AnimatedBuilder(
      animation: _mascotController,
      builder: (context, child) {
        final offset = -2.5 + (_mascotController.value * 5.0);

        return Transform.translate(offset: Offset(0, offset), child: child);
      },
      child: SizedBox(
        width: 92,
        height: 104,
        child: Stack(
          clipBehavior: Clip.none,
          alignment: Alignment.bottomCenter,
          children: [
            Positioned(
              bottom: 4,
              child: Container(
                width: 58,
                height: 14,
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.22),
                  borderRadius: BorderRadius.circular(50),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.16),
                      blurRadius: 14,
                      spreadRadius: 2,
                    ),
                  ],
                ),
              ),
            ),
            const Positioned(bottom: 10, child: MausamCloudMascot()),
          ],
        ),
      ),
    );
  }

  Widget _buildInput() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 6, 14, 14),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
          child: Container(
            padding: const EdgeInsets.fromLTRB(16, 6, 6, 6),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.09),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _sendMessage(),
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: const InputDecoration(
                      hintText: 'Ask about weather...',
                      hintStyle: TextStyle(color: Colors.white54, fontSize: 14),
                      border: InputBorder.none,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: _sendMessage,
                  icon: const Icon(
                    Icons.arrow_upward_rounded,
                    color: Colors.white,
                  ),
                  style: IconButton.styleFrom(
                    backgroundColor: Colors.white.withValues(alpha: 0.14),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ChatMessage {
  final String text;
  final bool isUser;

  const _ChatMessage({required this.text, required this.isUser});
}

class _ChatBubble extends StatelessWidget {
  final _ChatMessage message;

  const _ChatBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 310),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
        decoration: BoxDecoration(
          color: message.isUser
              ? Colors.white.withValues(alpha: 0.16)
              : Colors.white.withValues(alpha: 0.08),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(message.isUser ? 18 : 5),
            bottomRight: Radius.circular(message.isUser ? 5 : 18),
          ),
          border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.94),
            fontSize: 14,
            height: 1.45,
          ),
        ),
      ),
    );
  }
}

class _AtmosphericBackground extends StatelessWidget {
  const _AtmosphericBackground();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        children: [
          Positioned(
            top: -140,
            right: -100,
            child: Container(
              width: 330,
              height: 330,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF315D7A).withValues(alpha: 0.18),
              ),
            ),
          ),
          Positioned(
            bottom: -180,
            left: -120,
            child: Container(
              width: 380,
              height: 380,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF183D5A).withValues(alpha: 0.20),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
