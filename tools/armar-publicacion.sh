#!/bin/bash
#
# ARMA `dist/`: lo único que se publica del repo.
#
# POR QUÉ EXISTE. Cloudflare Pages publica la carpeta que uno le diga, y si se
# le dice la raíz publica el repo ENTERO: los 22 tableros de marca con sus
# notas internas, las páginas de prueba, los scripts, las migraciones. Nada de
# eso tiene secretos —el repo es público— pero **es andamiaje, y el andamiaje
# no va a la vidriera**: en el dominio del consultorio, una página que dice
# «Prueba · la pantalla ⑤» no se lee como herramienta, se lee como descuido.
#
# 🔑 Y HAY UN MOTIVO MÁS DURO QUE LA PROLIJIDAD: lo que se publica queda
# INDEXABLE. Sacar después una dirección que Google ya listó es más caro que no
# publicarla nunca.
#
# QUÉ SE PUBLICA, y la lista es explícita a propósito: lo que no esté acá NO
# llega al sitio. Es al revés de ignorar cosas una por una, donde el archivo
# nuevo se publica solo y nadie se entera.
#
#   · las tres páginas          · css/ y js/
#   · las dos fotos y los dos logos que el HTML usa
#   · las DOS TIPOGRAFÍAS y la lámina de íconos, que NO las nombra el HTML
#     sino el CSS
#
# 🔴 Y ESOS TRES ÚLTIMOS FALTABAN —1-oct-2026, los encontró Juan mirando el
# sitio publicado: «faltan íconos de las tarjetas de tratamientos»—. El sitio
# estuvo publicado un rato CON LAS TIPOGRAFÍAS CAÍDAS: Marcellus y Jost daban
# 404 y el navegador las reemplazaba por Georgia y Helvetica, que es
# exactamente el modo de falla que no grita. **Un archivo que sólo nombra el
# CSS no aparece en el HTML, así que ninguna lista escrita a ojo lo incluye.**
# Por eso el verificador de enlaces ahora también mira los `url( … )` del CSS.
#
# ⚠️ `brand/fotos/PROCEDENCIA.md` NO se copia aunque el HTML lo nombre en un
# comentario: es la ficha de dónde salió cada foto de banco, y es documentación
# del repo, no del sitio.
#
# CÓMO SE USA: lo corre Cloudflare en cada `git push` —es el «build command»—,
# y también se puede correr a mano para mirar qué quedaría:
#
#     bash tools/armar-publicacion.sh && ls -R dist

set -euo pipefail

cd "$( dirname "$0" )/.."

rm -rf dist
mkdir -p dist/css dist/js dist/brand/fotos dist/brand/logo/curvas dist/brand/fonts

cp index.html reservar.html mis-turnos.html dist/

cp css/tokens.css css/styles.css dist/css/
cp js/*.js dist/js/

cp brand/fotos/entrar-ejemplo.jpg brand/fotos/hero-ejemplo.jpg dist/brand/fotos/
cp brand/fotos/iconos-del-brief.png dist/brand/fotos/
cp brand/fonts/*.ttf dist/brand/fonts/
cp brand/logo/curvas/cb-apilado-curvas.svg brand/logo/curvas/cb-wordmark-curvas.svg dist/brand/logo/curvas/

echo "✓ dist/ armado"
du -sh dist
