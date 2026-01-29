# TODO - Mimo Tax Calculator

## High Priority

- [ ] **User Profile**: Agregar perfil de usuario para guardar preferencias
- [ ] **Session Persistence**: Si ya llené algo en los inputs no borrarlos al iniciar sesión
- [ ] **Responsive UI**: Mejorar el responsivo del sitio web (mobile-first)

## Medium Priority

- [ ] **Document Upload**: Opción para subir facturas (carpeta de documentos)
- [ ] **Bolsas Fiscales**: Implementar sistema de bolsas fiscales

## Low Priority / Ideas

- [ ] **Agent Intelligence**: Los agentes deben ser inteligentes para detectar los cambios en los inputs
- [ ] **UX Enhancement**: Hacer el feeling más agéntico y no tanto de calculadora
- [ ] ** Font **: Cambiar la fuente a https://r0xx.vercel.app/

## Completed ✅

- [x] **Tax Router Location**: El endpoint de `/calcular` debe estar en el módulo `tax_calculation` (DONE: `src/tax_calculation/infrastructure/api/tax_router.py`)
- [x] **App Version**: Mandar la versión de la app a un archivo de constantes (DONE: `src/shared/domain/constants/app_version.py`)
