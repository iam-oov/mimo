#!/bin/bash
# Script para generar tráfico y ver métricas en acción

echo "🚀 Generando tráfico para ver métricas..."
echo ""

# 1. Health checks
echo "📊 Haciendo 5 health checks..."
for i in {1..5}; do
    curl -s http://localhost:8000/health | jq -r '.status' && echo "  ✓ Health check $i OK"
    sleep 0.5
done

echo ""

# 2. Varios cálculos de impuestos
echo "💰 Haciendo 3 cálculos de impuestos..."
for i in {1..3}; do
    curl -s -X POST http://localhost:8000/api/calculate \
        -H "Content-Type: application/json" \
        -d '{
            "taxpayer_name": "Test User '$i'",
            "fiscal_year": 2026,
            "monthly_gross_income": '$((50000 + i * 10000))',
            "monthly_net_income": 0,
            "bonus_days": 15,
            "vacation_days": 12,
            "vacation_premium_percentage": 0.25,
            "general_deductions": '$((20000 + i * 5000))',
            "total_tuition": 0,
            "total_ppr": 0
        }' | jq -r '.annual_tax_payable' && echo "  ✓ Cálculo $i completado"
    sleep 1
done

echo ""
echo "✅ Tráfico generado!"
echo ""
echo "🔍 Ahora ve a:"
echo "  - Prometheus: http://localhost:9090 → Busca 'mimo_http_requests_total'"
echo "  - Grafana: http://localhost:3000 → Dashboard 'Mimo Overview'"
