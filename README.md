# Ecos del Umbral

Videojuego de aventura y supervivencia hecho desde cero con Python, Pygame y mapas TMX cargados con pytmx. Explora cinco zonas, derrota enemigos, reúne recursos y activa los mecanismos para escapar del Umbral.

## Requisitos

- Python 3.10 o posterior
- Pygame 2.5 o posterior
- pytmx 3.32 o posterior

## Ejecutar

Desde esta carpeta:

```powershell
python -m pip install -r requirements.txt
python main.py
```

En Windows también puedes ejecutar `iniciar.bat`.

## Controles

| Acción | Teclado |
| --- | --- |
| Moverse | WASD o flechas |
| Atacar | Espacio |
| Saltar | J |
| Disparar | F |
| Interactuar / abrir puerta | E |
| Usar el objeto seleccionado | Q |
| Seleccionar objeto | 1–4 o rueda del ratón |
| Pausar / volver | Escape |

El inventario muestra los objetos guardados. Las pociones y los potenciadores se usan con Q; las llaves se usan al interactuar con una puerta. En el menú de pausa puedes descartar el objeto seleccionado con X.

## Progreso

Derrota a los enemigos de cada zona, consigue la llave o activa el mecanismo indicado y usa E junto a la puerta. Las cinco zonas tienen mapas TMX independientes, música, coleccionables y dificultad creciente. Las instrucciones contextuales aparecen durante los primeros niveles.

## Configuración

Desde el menú principal puedes ajustar volumen, resolución, distribución de controles y dificultad. La ventana se puede cambiar de tamaño; la cámara sigue al jugador en mapas más grandes que la ventana.

## Estructura

- `main.py`: inicio y bucle principal
- `game/`: jugador, enemigos, mapas, interfaz, audio y estado global
- `assets/maps/`: cinco mapas `.tmx` editables en Tiled
- `assets/tilesets/`: atlas y definiciones Tiled para bosque, desierto, catacumbas, pantano y Umbral
- `assets/sprites/player/`: hojas de animación del personaje
- `tools/build_maps.py`: reconstruye los atlas y los cinco mapas TMX
- `tests/`: pruebas automáticas

Los mapas están hechos con el formato TMX de Tiled y se cargan en ejecución mediante pytmx. Para editarlos, abre los archivos de `assets/maps/` en Tiled Map Editor.

## Arte visual

El jugador principal utiliza el personaje Hooded Blade con animaciones de reposo, carrera, ataque y salto. Sus hojas originales y metadatos están en `assets/sprites/player/hooded-blade/`; el arte se distribuye bajo CC0 y su licencia se incluye con los recursos. El ataque también representa visualmente el disparo. Cada nivel tiene un trazado, paleta y tileset propios; los atlas se generan desde las imágenes fuente incluidas en `assets/tilesets/source/`. El tileset Tiny Dungeon de Kenney se distribuye bajo licencia CC0; se incluye su licencia junto a las fuentes.

## Sonido

La banda sonora y los efectos son composiciones originales generadas en el proyecto como archivos WAV. Cinco temas tienen identidad distinta y se reproducen según la zona. No utiliza pistas comerciales ni requiere conexión a internet.
