# Ajuste exclusivo de CROUCH

El puente de acciones conserva la referencia neutral de hombros/caderas ya calibrada.
No recalibra ni modifica el detector MediaPipe, el clasificador lateral o JUMP.

Las medidas se normalizan por la altura neutral del torso:

- Inclinación: altura proyectada del torso inferior al 85% y descenso
  de hombros superior al 12%.
- Agachado: descenso de hombros superior al 12% y de caderas superior al 8%,
  aunque la altura proyectada del torso no se comprima.
- Confirmación: tres lecturas consecutivas fiables.
- Histéresis: con CROUCH activo, límites de 90%, 7% y 5%, respectivamente.
- Retención: 0,70 segundos desde la última postura válida de CROUCH.

## Validación

`python utils/test_body_action_bridge.py`: doce pruebas pasan, incluyendo postura
neutral, pulsos aislados, inclinación moderada, agachado, histéresis, retención y JUMP.

`python utils/verify_final_adjustments.py`: ejecuta Ursina, calibra una postura neutral
con landmarks sintéticos y transmite una inclinación moderada por el clasificador y
el puente reales hasta Player. Se combina descenso de hombros de 15% y de caderas
de 9% del torso neutral. CROUCH se activa y se verifican en orden los índices
0, 1 y 2 de la animación. Capturas inspeccionadas: `crouch_01.png`, `crouch_02.png`,
`crouch_03.png`. Se conserva la referencia calibrada, pasa el pórtico y vuelve a RUN
después de la retención. También pasan LEFT/RIGHT y JUMP.

Esta comprobación usa landmarks simulados; falta confirmar la sensibilidad con la
postura real del usuario frente a su cámara.

## Depuración temporal en PowerShell

La consola permanece silenciosa por defecto. Para probar con mediciones de torso:

```powershell
$env:HK_DEBUG_CROUCH = '1'
python main.py
Remove-Item Env:HK_DEBUG_CROUCH
```

Las mediciones salen cada 0,25 segundos: relación de altura del torso, descenso de
hombros/caderas, lecturas consecutivas y señal activa. La prueba automatizada activa
estas mediciones solo durante su tramo de CROUCH.
