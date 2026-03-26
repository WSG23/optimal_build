from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.ai import multi_modal_analyzer


@pytest.mark.asyncio
async def test_remote_image_urls_are_not_fetched_or_sent_to_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm = MagicMock()
    monkeypatch.setattr(
        multi_modal_analyzer,
        "ChatOpenAI",
        MagicMock(return_value=llm),
    )

    service = multi_modal_analyzer.MultiModalAnalyzerService()
    result = await service.analyze(
        multi_modal_analyzer.AnalysisRequest(
            image_url="https://example.com/site.jpg",
            image_type=multi_modal_analyzer.ImageType.SITE_PHOTO,
            analysis_types=[multi_modal_analyzer.AnalysisType.CONDITION_ASSESSMENT],
        )
    )

    assert result.confidence == 0.0
    llm.invoke.assert_not_called()
