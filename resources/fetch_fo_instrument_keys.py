"""
Script to fetch instrument keys for all F&O eligible stocks
and update the upstox_integration.py file
"""

import json
import requests
import os

# Read F&O stocks
with open('fo_stocks.json', 'r') as f:
    fo_data = json.load(f)

# Known ISIN codes for popular F&O stocks (manually curated)
# Source: NSE/BSE websites
ISIN_MAPPING = {
    'RELIANCE': 'INE002A01018',
    'TCS': 'INE467B01029',
    'INFY': 'INE009A01021',
    'HDFCBANK': 'INE040A01034',
    'ICICIBANK': 'INE090A01021',
    'SBIN': 'INE062A01020',
    'BHARTIARTL': 'INE397D01024',
    'ITC': 'INE154A01025',
    'WIPRO': 'INE075A01022',
    'LT': 'INE018A01030',
    'AXISBANK': 'INE238A01034',
    'MARUTI': 'INE585B01010',
    'SUNPHARMA': 'INE044A01036',
    'TATAMOTORS': 'INE155A01022',
    'TATASTEEL': 'INE081A01020',
    'HINDUNILVR': 'INE030A01027',
    'M&M': 'INE101A01026',
    'KOTAKBANK': 'INE237A01028',
    'ADANIENT': 'INE423A01024',
    'INDUSINDBK': 'INE095A01012',
    'ASIANPAINT': 'INE021A01026',
    'BAJAJ-AUTO': 'INE917I01010',
    'BAJFINANCE': 'INE296A01024',
    'BAJAJFINSV': 'INE918I01018',
    'BPCL': 'INE029A01011',
    'BRITANNIA': 'INE216A01030',
    'CIPLA': 'INE059A01026',
    'COALINDIA': 'INE522F01014',
    'DIVISLAB': 'INE361B01024',
    'DRREDDY': 'INE089A01023',
    'EICHERMOT': 'INE066A01021',
    'GRASIM': 'INE047A01021',
    'HCLTECH': 'INE860A01027',
    'HEROMOTOCO': 'INE158A01026',
    'HINDALCO': 'INE038A01020',
    'JSWSTEEL': 'INE019A01038',
    'NTPC': 'INE733E01010',
    'ONGC': 'INE213A01029',
    'POWERGRID': 'INE752E01010',
    'SHREECEM': 'INE070A01015',
    'TECHM': 'INE669C01036',
    'TITAN': 'INE280A01028',
    'ULTRACEMCO': 'INE481G01011',
    'UPL': 'INE628A01036',
    'VEDL': 'INE205A01025',
    'ADANIPORTS': 'INE742F01042',
    'APOLLOHOSP': 'INE437A01024',
    'BANDHANBNK': 'INE545U01014',
    'BERGEPAINT': 'INE463A01038',
    'BEL': 'INE263A01024',
    'BOSCHLTD': 'INE323A01026',
    'CANBK': 'INE476A01022',
    'CHOLAFIN': 'INE121A01024',
    'DABUR': 'INE016A01026',
    'DLF': 'INE271C01023',
    'GAIL': 'INE129A01019',
    'GODREJCP': 'INE102D01028',
    'HAVELLS': 'INE176B01034',
    'HDFCLIFE': 'INE795G01014',
    'ICICIPRULI': 'INE726G01019',
    'INDIGO': 'INE646L01027',
    'IOC': 'INE242A01010',
    'IRCTC': 'INE335Y01020',
    'JINDALSTEL': 'INE749A01030',
    'MOTHERSON': 'INE775A01035',
    'MUTHOOTFIN': 'INE414G01012',
    'NMDC': 'INE584A01023',
    'NAUKRI': 'INE663F01024',
    'NESTLEIND': 'INE239A01016',
    'PAYTM': 'INE982J01020',
    'PERSISTENT': 'INE262H01013',
    'PFC': 'INE134E01011',
    'PIIND': 'INE603J01030',
    'PNB': 'INE160A01022',
    'RECLTD': 'INE020B01018',
    'SBICARD': 'INE018E01016',
    'SBILIFE': 'INE123W01016',
    'SIEMENS': 'INE003A01024',
    'TATACONSUM': 'INE192A01025',
    'TATAPOWER': 'INE245A01021',
    'TORNTPHARM': 'INE685A01028',
    'TRENT': 'INE849A01020',
    'VOLTAS': 'INE226A01021',
    'ZEEL': 'INE256A01028',
    'ZOMATO': 'INE758T01015',
    'ABFRL': 'INE647O01011',
    'ABBOTINDIA': 'INE358A01014',
    'ACC': 'INE012A01025',
    'ADANITRANS': 'INE640H01013',
    'ALKEM': 'INE540L01014',
    'AMBUJACEM': 'INE079A01024',
    'APOLLOTYRE': 'INE438A01022',
    'ASHOKLEY': 'INE208A01029',
    'AUROPHARMA': 'INE406A01037',
    'BALKRISIND': 'INE787D01026',
    'BATAINDIA': 'INE176A01028',
    'BHARATFORG': 'INE465A01025',
    'BIOCON': 'INE376G01013',
    'CUMMINSIND': 'INE298A01020',
    'COLPAL': 'INE259A01022',
    'CONCOR': 'INE111A01025',
    'COFORGE': 'INE591G01017',
    'ESCORTS': 'INE042A01014',
    'EXIDEIND': 'INE302A01020',
    'FEDERALBNK': 'INE171A01029',
    'GMRINFRA': 'INE776C01039',
    'GNFC': 'INE113A01013',
    'GODREJPROP': 'INE484J01027',
    'GUJGASLTD': 'INE844O01030',
    'HINDZINC': 'INE267A01025',
    'IBULHSGFIN': 'INE148I01020',
    'IDFC': 'INE043D01016',
    'IDFCFIRSTB': 'INE092T01019',
    'IGL': 'INE203G01027',
    'INDHOTEL': 'INE053A01029',
    'INDUSTOWER': 'INE121J01017',
    'JUBLFOOD': 'INE797F01020',
    'LICHSGFIN': 'INE115A01026',
    'LTIM': 'INE214T01019',
    'LUPIN': 'INE326A01037',
    'MANAPPURAM': 'INE522D01027',
    'MARICO': 'INE196A01026',
    'MCDOWELL-N': 'INE854D01024',
    'MFSL': 'INE180A01020',
    'MGL': 'INE002S01010',
    'NAVINFLUOR': 'INE048G01026',
    'OBEROIRLTY': 'INE093I01010',
    'OFSS': 'INE881D01027',
    'PETRONET': 'INE347G01014',
    'PFIZER': 'INE182A01018',
    'PIDILITIND': 'INE318A01026',
    'PVR': 'INE191H01014',
    'RBLBANK': 'INE976G01028',
    'SRTRANSFIN': 'INE804I01017',
    'SAIL': 'INE114A01011',
    'SUNTV': 'INE424H01027',
    'TORNTPOWER': 'INE813H01021',
    'TVSMOTOR': 'INE494B01023',
    'UBL': 'INE358A01014',
    'MPHASIS': 'INE356A01018',
    'AUBANK': 'INE949L01017',
    'BANDHANBNK': 'INE545U01014',
    'CROMPTON': 'INE299U01018',
    'DALBHARAT': 'INE771A01020',
    'DIXON': 'INE935N01012',
    'HAL': 'INE066F01020',
    'IRFC': 'INE053F01010',
    'METROPOLIS': 'INE112L01020',
    'POLYCAB': 'INE455K01017',
    'LAURUSLABS': 'INE947Q01028',
}

# Generate instrument keys
instrument_keys = {}
for stock in fo_data['stocks']:
    symbol = stock['nse_symbol']
    if symbol in ISIN_MAPPING:
        instrument_key = f"NSE_EQ|{ISIN_MAPPING[symbol]}"
        instrument_keys[symbol] = instrument_key

print(f"✅ Generated instrument keys for {len(instrument_keys)} out of {len(fo_data['stocks'])} F&O stocks")
print(f"⚠️ Missing ISIN codes for {len(fo_data['stocks']) - len(instrument_keys)} stocks")

# Save to JSON file
output = {
    'generated_at': '2025-12-11',
    'total_fo_stocks': len(fo_data['stocks']),
    'mapped_stocks': len(instrument_keys),
    'instrument_keys': instrument_keys
}

with open('fo_instrument_keys.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n💾 Saved to fo_instrument_keys.json")

# Generate Python code for upstox_integration.py
print("\n" + "="*80)
print("📝 Python code to add to upstox_integration.py:")
print("="*80)
print("\nSTOCK_INSTRUMENT_KEYS = {")
for symbol, key in sorted(instrument_keys.items()):
    print(f"    '{symbol}': '{key}',")
print("}")
print("\n" + "="*80)

# List missing stocks
missing = [stock['nse_symbol'] for stock in fo_data['stocks'] if stock['nse_symbol'] not in ISIN_MAPPING]
if missing:
    print(f"\n⚠️ Missing ISIN codes for {len(missing)} stocks:")
    for i, symbol in enumerate(missing[:20], 1):
        print(f"  {i}. {symbol}")
    if len(missing) > 20:
        print(f"  ... and {len(missing) - 20} more")
