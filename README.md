# DECO Subsea · container en rigging pagina's

Publieke pagina's achter de QR codes op de containers van DECO Subsea.
Elke container heeft een vaste map `container/<containernummer>/`. De code verandert nooit, zodat de QR op het label altijd geldig blijft.

## Certificaten van een container toevoegen
1. Open de map `container/<containernummer>/certificaten/` van de container.
2. Klik op **Add file** > **Upload files** en sleep de PDF erin.
3. Klik op **Commit changes**. De PDF verschijnt op de pagina nadat de pagina's opnieuw gebouwd zijn.

De gegevens (gewichten, sling, shackles) komen uit RigTrack en worden met `tools/build_site.py` bijgewerkt.
