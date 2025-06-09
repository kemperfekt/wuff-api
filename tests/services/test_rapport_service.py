# tests/services/test_rapport_service.py
"""
Tests for MVP RapportEnhancer service.
"""

import pytest
from src.services.rapport_service import RapportEnhancer


class TestRapportEnhancer:
    """Test cases for RapportEnhancer service."""
    
    def setup_method(self):
        """Set up test instance."""
        self.enhancer = RapportEnhancer()
    
    def test_basic_enhancement(self):
        """Test basic response enhancement."""
        response = "Das ist ein typisches Hundeverhalten."
        enhanced = self.enhancer.enhance_response(response)
        
        # Should add presence marker
        assert enhanced != response
        assert "*" in enhanced
        assert response in enhanced
    
    def test_emotion_detection(self):
        """Test emotion detection from user input."""
        test_cases = [
            ("Ich bin total verzweifelt!", "concerned"),
            ("Das ist toll!", "engaged"),
            ("Warum macht er das?", "thoughtful"),
            ("Hallo", "calm")
        ]
        
        for user_input, expected_emotion in test_cases:
            detected = self.enhancer._detect_simple_emotion(user_input)
            assert detected == expected_emotion
    
    def test_presence_markers_by_emotion(self):
        """Test that different emotions get different markers."""
        response = "Test response"
        
        # Test different emotional contexts
        calm_enhanced = self.enhancer.enhance_response(response, emotional_context="calm")
        concerned_enhanced = self.enhancer.enhance_response(response, emotional_context="concerned")
        
        # Both should be enhanced but differently
        assert "*" in calm_enhanced
        assert "*" in concerned_enhanced
        assert response in calm_enhanced
        assert response in concerned_enhanced
    
    def test_empty_response_handling(self):
        """Test handling of empty or short responses."""
        # Empty response
        assert self.enhancer.enhance_response("") == ""
        
        # Very short response
        short = "Ok."
        assert self.enhancer.enhance_response(short) == short
    
    def test_available_emotions(self):
        """Test getting available emotion categories."""
        emotions = self.enhancer.get_available_emotions()
        
        expected_emotions = ["calm", "concerned", "engaged", "thoughtful"]
        assert all(emotion in emotions for emotion in expected_emotions)
    
    def test_emotion_validation(self):
        """Test emotion category validation."""
        assert self.enhancer.validate_emotion("calm") is True
        assert self.enhancer.validate_emotion("invalid") is False
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        health = await self.enhancer.health_check()
        
        assert health["status"] == "healthy"
        assert health["service"] == "RapportEnhancer"
        assert "markers_loaded" in health
        assert health["test_enhancement"] == "✅"
    
    def test_error_handling(self):
        """Test error handling in enhancement."""
        # This should not crash even with None input
        result = self.enhancer.enhance_response(None)
        assert result is None or result == ""
    
    def test_integration_example(self):
        """Test realistic usage example."""
        user_input = "Mein Hund bellt ständig an der Tür!"
        response = "Das ist ein Territorialverhalten. Dein Hund beschützt sein Zuhause."
        
        enhanced = self.enhancer.enhance_response(response, user_input)
        
        # Should detect "ständig" as stressed -> concerned
        # Should add appropriate presence marker
        assert "*" in enhanced
        assert response in enhanced
        assert enhanced.startswith("*")
    
    def test_multiple_enhancements_variation(self):
        """Test that multiple enhancements vary (random markers)."""
        response = "Das ist ein Test."
        
        # Run enhancement multiple times
        enhancements = [
            self.enhancer.enhance_response(response, emotional_context="calm")
            for _ in range(10)
        ]
        
        # All should be enhanced
        assert all("*" in e for e in enhancements)
        
        # Should have some variation (random selection)
        # Note: With only 6 calm markers, we might get repeats, 
        # but very unlikely to get ALL the same
        unique_enhancements = set(enhancements)
        assert len(unique_enhancements) > 1  # Should have some variation