# 🔐 Guía Completa: Configurar Google OAuth2 para MIMO Tax Calculator

## 📋 Pasos Detallados

### 1. **Accede a Google Cloud Console**

- Ve a: https://console.cloud.google.com/
- Inicia sesión con tu cuenta de Gmail

### 2. **Crear/Seleccionar Proyecto**

- Click en el selector de proyectos (arriba a la izquierda)
- Si no tienes proyecto: "New Project"
- Nombre: "MIMO Tax Calculator"
- Click "Create"

### 3. **Habilitar APIs Necesarias**

- Ve a: **APIs & Services > Library**
- Buscar y habilitar:
  - ✅ **Google Identity API**
  - ✅ **Google+ API** (legacy pero necesaria)

### 4. **Configurar Pantalla de Consentimiento**

- Ve a: **APIs & Services > OAuth consent screen**
- Selecciona: **External**
- Llena los campos obligatorios:
  - **App name**: MIMO Tax Calculator
  - **User support email**: tu-email@gmail.com
  - **Developer contact information**: tu-email@gmail.com
- Click "Save and Continue" en cada pantalla

### 5. **Crear Credenciales OAuth2**

- Ve a: **APIs & Services > Credentials**
- Click: **Create Credentials > OAuth 2.0 Client ID**
- **Application type**: Web application
- **Name**: MIMO Web Client
- **Authorized redirect URIs**:
  ```
  http://localhost:8000/auth/callback
  ```
- Click **Create**

### 6. **Copiar Credenciales**

Se mostrará una ventana popup con:

- **Client ID**: `123456789-abcd1234.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-abcd1234efgh5678`

### 7. **Actualizar archivo .env**

En tu archivo `.env`, reemplaza:

```bash
GOOGLE_CLIENT_ID=tu-client-id-real-aqui.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-tu-client-secret-real-aqui
```

### 8. **Reiniciar Servidor**

```bash
# Reiniciar el servidor para cargar las nuevas credenciales
uv run python server.py
```

### 9. **Probar Login**

- Ve a: http://localhost:8000/login
- Click "Continue with Google"
- Debería redirigir a Google y pedir permisos

## 🎯 URLs Importantes

- **Google Cloud Console**: https://console.cloud.google.com/
- **Tu App (Login)**: http://localhost:8000/login
- **Tu App (Calculator)**: http://localhost:8000/calculator

## ⚠️ Notas Importantes

- La Google+ API está deprecada pero algunos flujos OAuth aún la requieren
- Usa "External" en OAuth consent para poder usar cualquier Gmail
- El redirect URI debe ser exactamente: `http://localhost:8000/auth/callback`
- Las credenciales son sensibles, nunca las compartas públicamente

## 🔧 Solución de Problemas

Si tienes errores:

1. Verifica que las URLs de redirect sean exactas
2. Asegúrate de habilitar ambas APIs
3. Usa "External" en OAuth consent screen
4. Reinicia el servidor después de cambiar .env
