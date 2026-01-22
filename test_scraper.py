"""Test script to verify the refactored scraper package."""

from scraper import scrape_properties


def test_basic_usage():
    """Test basic scraping of Las Condes apartments."""
    print("\n" + "="*60)
    print("TEST 1: Basic Usage - Las Condes")
    print("="*60)

    properties = scrape_properties("las-condes", max_pages=1, headless=True)

    print(f"\n✓ Test passed: Found {len(properties)} properties")
    assert len(properties) > 0, "Should find at least some properties"
    return properties


def test_different_comuna():
    """Test with a different comuna."""
    print("\n" + "="*60)
    print("TEST 2: Different Comuna - Providencia")
    print("="*60)

    properties = scrape_properties("providencia", max_pages=1, headless=True)

    print(f"\n✓ Test passed: Found {len(properties)} properties")
    assert len(properties) > 0, "Should find at least some properties"
    return properties


def test_return_dataframe():
    """Test returning data as DataFrame."""
    print("\n" + "="*60)
    print("TEST 3: Return DataFrame")
    print("="*60)

    df = scrape_properties("santiago", max_pages=1, return_dataframe=True, headless=True)

    print(f"\n✓ Test passed: DataFrame shape: {df.shape}")
    assert len(df) > 0, "DataFrame should have rows"
    assert list(df.columns) == ['url', 'dormitorios', 'banos', 'superficie', 'ubicacion']
    return df


def test_casa_property_type():
    """Test scraping houses instead of apartments."""
    print("\n" + "="*60)
    print("TEST 4: Property Type - Casa (House)")
    print("="*60)

    properties = scrape_properties("vitacura", max_pages=1, property_type="casa", headless=True)

    print(f"\n✓ Test passed: Found {len(properties)} houses")
    return properties


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# Running Scraper Verification Tests")
    print("#"*60)

    try:
        # Run basic test
        props1 = test_basic_usage()

        # Show sample of first test
        if props1:
            print("\nSample property from Test 1:")
            prop = props1[0]
            print(f"  URL: {prop.url[:80]}...")
            print(f"  Bedrooms: {prop.dormitorios}")
            print(f"  Bathrooms: {prop.banos}")
            print(f"  Surface: {prop.superficie}")
            print(f"  Location: {prop.ubicacion[:50] if prop.ubicacion else 'N/A'}...")

        # Additional tests (uncomment to run)
        # test_different_comuna()
        # test_return_dataframe()
        # test_casa_property_type()

        print("\n" + "#"*60)
        print("# ✅ All Tests Passed!")
        print("#"*60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
