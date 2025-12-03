from app import get_timocom_pricing, get_transeu_pricing, postal_code_to_region_id

# Test mapowania
start_region = postal_code_to_region_id('DE49')
end_region = postal_code_to_region_id('PL20')

print(f"DE49 -> region_id: {start_region}")
print(f"PL20 -> region_id: {end_region}")
print()

# Test TimoCom
print("="*60)
print("Test TimoCom dla DE49 (region 98) -> PL20 (region 135)")
print("="*60)
timocom_result = get_timocom_pricing(start_region, end_region, days=7)
if timocom_result:
    print("✅ TimoCom zwrócił dane:")
    print(timocom_result)
else:
    print("❌ TimoCom zwrócił None")

print()

# Test Trans.eu
print("="*60)
print("Test Trans.eu dla DE49 (region 98) -> PL20 (region 135)")
print("="*60)
transeu_result = get_transeu_pricing(start_region, end_region, days=7)
if transeu_result:
    print("✅ Trans.eu zwrócił dane:")
    print(transeu_result)
else:
    print("❌ Trans.eu zwrócił None")
