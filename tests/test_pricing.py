from multi_coder_analysis.pricing import estimate_cost

def test_cost_roundtrip():
    out = estimate_cost(
        provider="gemini",
        model="gemini-2.5-flash",
        prompt_tokens=1000,
        response_tokens=500,
        cached_tokens=200,
    )
    # Expected costs
    billed_in = 800  # prompt minus cached
    cost = (billed_in * 0.30 + 200 * 0.30 * 0.25 + 500 * 2.50) / 1_000_000
    assert abs(out["cost_total_usd"] - cost) < 1e-9 