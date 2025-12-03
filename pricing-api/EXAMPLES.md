# Przykłady użycia Pricing API

## cURL

### Test Health Check
```bash
curl http://localhost:5001/health
```

### Podstawowe zapytanie
```bash
curl -X POST http://localhost:5001/api/pricing \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'
```

### Z formatowaniem (jq)
```bash
curl -X POST http://localhost:5001/api/pricing \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}' | jq
```

## Python

### Podstawowe użycie
```python
import requests

response = requests.post(
    'http://localhost:5001/api/pricing',
    json={
        'start_postal_code': 'PL50',
        'end_postal_code': 'DE10'
    }
)

if response.status_code == 200:
    data = response.json()['data']
    print(f"Region IDs: {data['start_region_id']} -> {data['end_region_id']}")
    
    # TimoCom 7 dni
    if 'timocom' in data['pricing'] and '7d' in data['pricing']['timocom']:
        timocom_7d = data['pricing']['timocom']['7d']
        print(f"TimoCom trailer avg: {timocom_7d['avg_price_per_km']['trailer']} EUR/km")
        print(f"Oferty: {timocom_7d['total_offers']}")
else:
    print(f"Błąd: {response.json()['error']}")
```

### Przetwarzanie wszystkich okresów
```python
import requests

def get_pricing(start, end):
    response = requests.post(
        'http://localhost:5001/api/pricing',
        json={
            'start_postal_code': start,
            'end_postal_code': end
        }
    )
    return response.json()

# Pobierz dane
result = get_pricing('PL50', 'DE10')

if result['success']:
    pricing = result['data']['pricing']
    
    # TimoCom - wszystkie okresy
    print("\n📊 TimoCom:")
    for period in ['7d', '30d', '90d']:
        if period in pricing.get('timocom', {}):
            data = pricing['timocom'][period]
            avg = data['avg_price_per_km']
            median = data['median_price_per_km']
            
            print(f"\n{period}:")
            print(f"  Trailer: avg={avg.get('trailer')}, median={median.get('trailer')}")
            print(f"  3.5t: avg={avg.get('3_5t')}, median={median.get('3_5t')}")
            print(f"  12t: avg={avg.get('12t')}, median={median.get('12t')}")
            print(f"  Oferty: {data['total_offers']}, Dni: {data['days_with_data']}")
    
    # Trans.eu - wszystkie okresy
    print("\n📊 Trans.eu:")
    for period in ['7d', '30d', '90d']:
        if period in pricing.get('transeu', {}):
            data = pricing['transeu'][period]
            avg = data['avg_price_per_km']
            median = data['median_price_per_km']
            
            print(f"\n{period}:")
            print(f"  Lorry: avg={avg.get('lorry')}, median={median.get('lorry')}")
            print(f"  Dni: {data['days_with_data']}")
```

### Batch processing wielu tras
```python
import requests
from concurrent.futures import ThreadPoolExecutor

def get_route_pricing(route):
    start, end = route
    response = requests.post(
        'http://localhost:5001/api/pricing',
        json={
            'start_postal_code': start,
            'end_postal_code': end
        }
    )
    return {
        'route': f"{start} -> {end}",
        'success': response.status_code == 200,
        'data': response.json()
    }

# Lista tras
routes = [
    ('PL50', 'DE10'),
    ('PL00', 'DE01'),
    ('PL52', 'FR75'),
    ('DE10', 'IT20'),
]

# Równoległe przetwarzanie
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(get_route_pricing, routes))

# Wyświetl wyniki
for result in results:
    print(f"\n{result['route']}: {'✅' if result['success'] else '❌'}")
    if result['success']:
        data = result['data']['data']
        if 'timocom' in data['pricing'] and '7d' in data['pricing']['timocom']:
            tc = data['pricing']['timocom']['7d']
            print(f"  TimoCom 7d: {tc['avg_price_per_km']['trailer']} EUR/km")
```

## JavaScript / Node.js

### Fetch API
```javascript
async function getPricing(startPostal, endPostal) {
  const response = await fetch('http://localhost:5001/api/pricing', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      start_postal_code: startPostal,
      end_postal_code: endPostal
    })
  });
  
  return await response.json();
}

// Użycie
getPricing('PL50', 'DE10')
  .then(result => {
    if (result.success) {
      const pricing = result.data.pricing;
      
      // TimoCom 7 dni
      if (pricing.timocom && pricing.timocom['7d']) {
        const tc7d = pricing.timocom['7d'];
        console.log('TimoCom 7d trailer:', tc7d.avg_price_per_km.trailer, 'EUR/km');
        console.log('Oferty:', tc7d.total_offers);
      }
      
      // Trans.eu 7 dni
      if (pricing.transeu && pricing.transeu['7d']) {
        const te7d = pricing.transeu['7d'];
        console.log('Trans.eu 7d lorry:', te7d.avg_price_per_km.lorry, 'EUR/km');
      }
    } else {
      console.error('Błąd:', result.error);
    }
  });
```

### Axios
```javascript
const axios = require('axios');

async function getPricing(startPostal, endPostal) {
  try {
    const response = await axios.post('http://localhost:5001/api/pricing', {
      start_postal_code: startPostal,
      end_postal_code: endPostal
    });
    
    return response.data;
  } catch (error) {
    if (error.response) {
      return error.response.data;
    }
    throw error;
  }
}

// Użycie
(async () => {
  const result = await getPricing('PL50', 'DE10');
  console.log(JSON.stringify(result, null, 2));
})();
```

## PHP

### file_get_contents
```php
<?php

function getPricing($startPostal, $endPostal) {
    $url = 'http://localhost:5001/api/pricing';
    
    $data = json_encode([
        'start_postal_code' => $startPostal,
        'end_postal_code' => $endPostal
    ]);
    
    $options = [
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => $data
        ]
    ];
    
    $context = stream_context_create($options);
    $response = file_get_contents($url, false, $context);
    
    return json_decode($response, true);
}

// Użycie
$result = getPricing('PL50', 'DE10');

if ($result['success']) {
    $pricing = $result['data']['pricing'];
    
    if (isset($pricing['timocom']['7d'])) {
        $tc7d = $pricing['timocom']['7d'];
        echo "TimoCom 7d trailer: " . $tc7d['avg_price_per_km']['trailer'] . " EUR/km\n";
        echo "Oferty: " . $tc7d['total_offers'] . "\n";
    }
}
?>
```

### cURL (PHP)
```php
<?php

function getPricing($startPostal, $endPostal) {
    $url = 'http://localhost:5001/api/pricing';
    
    $data = json_encode([
        'start_postal_code' => $startPostal,
        'end_postal_code' => $endPostal
    ]);
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($data)
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    return [
        'status_code' => $httpCode,
        'data' => json_decode($response, true)
    ];
}

// Użycie
$result = getPricing('PL50', 'DE10');

if ($result['status_code'] == 200 && $result['data']['success']) {
    print_r($result['data']['data']['pricing']);
}
?>
```

## Postman Collection

### Request
```json
{
  "info": {
    "name": "Pricing API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Pricing",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"start_postal_code\": \"PL50\",\n  \"end_postal_code\": \"DE10\"\n}"
        },
        "url": {
          "raw": "http://localhost:5001/api/pricing",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5001",
          "path": ["api", "pricing"]
        }
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": {
          "raw": "http://localhost:5001/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5001",
          "path": ["health"]
        }
      }
    }
  ]
}
```

## Excel / VBA

```vba
Sub GetPricing()
    Dim http As Object
    Dim json As String
    Dim url As String
    
    Set http = CreateObject("MSXML2.XMLHTTP")
    
    url = "http://localhost:5001/api/pricing"
    json = "{""start_postal_code"": ""PL50"", ""end_postal_code"": ""DE10""}"
    
    http.Open "POST", url, False
    http.setRequestHeader "Content-Type", "application/json"
    http.send json
    
    If http.Status = 200 Then
        MsgBox http.responseText
    Else
        MsgBox "Błąd: " & http.Status
    End If
End Sub
```

## PowerShell

```powershell
$body = @{
    start_postal_code = "PL50"
    end_postal_code = "DE10"
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:5001/api/pricing" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"

if ($response.success) {
    Write-Host "Region IDs: $($response.data.start_region_id) -> $($response.data.end_region_id)"
    
    $tc7d = $response.data.pricing.timocom.'7d'
    Write-Host "TimoCom 7d trailer: $($tc7d.avg_price_per_km.trailer) EUR/km"
    Write-Host "Oferty: $($tc7d.total_offers)"
}
```
