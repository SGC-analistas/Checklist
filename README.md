![SGC](images/sgc_logo.png)<!-- .element width="700"-->

# Checklist

Rutina realizada para hacer el checklist de las estaciones de la RSNC, RNAC,INTER. 

Se basa en hacerle slinktool a todas las estaciones en dos ocasiones. 
La idea es tener la diferencia de tiempo de los slinktool. Si la diferencia de tiempo 
es mayor al valor del argumento *dt* que por defecto esta en *120s* entonces esta
por *offline* o *recovering*, depende si la diferencia de tiempo es *0 s* esta offline,
si la diferencia de tiempo es *>0 s* esta recovering.

**SI ESTA EN EL PROC 4, NO ES NECESARIO REVISAR LA SECCIÓN DE INSTALACIÓN**

## 1. Instalación en linux

### Requerimientos previos
Se corre en sistemas linux.

### - Python
Python Versión 3.7 en adelante. (Usaremos como ejemplo python 3.8)
```bash
sudo apt-get install python3.7 (o 3.8)
```

Tener virtualenv en python.
```bash
python3.7 -m pip install virtualenv
```

### Instalación con pip 

```bash
conda deactivate #En caso de que haya un ambiente de anaconda activo
python3.7 -m virtualenv .checklist
source .checklist/bin/activate
pip install -r requirements.txt
```

## 2. Instrucciones de uso
### Comandos de uso
Con +h se pide ayuda.
```bash
  +online , ++online    Tiempo de actualización en segundos
  +dt , ++delta_time    Limite de tiempo en segundos para decir que esta por fuera
  +server , ++server    Servidor donde se hace la consulta
  +net, ++network       Filtrar por redes. Ejemplo: 'CM' 'OM' 'OP'
  +loc, ++location      Filtrar por localización. Ejemplo: '00' ' ' '20'
  +status, ++status     Filtrar por estado. Ejemplo: 'offline' 'recovering'
  +a , ++add            Agregar información en RSNC, RNAC o INTER
```
## 3. Ejemplos
### Ejemplo 1: checklist
Trae todas las estaciones de todas las redes, todos los estados.
```bash
    python checklist.py 
```

### Ejemplo 2: checklist
Filtrar redes: *CM*, estado: *offline* *recovering*
```bash
    python checklist.py +net CM +status offline recovering
```

### Ejemplo 3: Cosas varias
Fijar el limite de tiempo en 600 segundos para decir que esta por fuera. *dt 600*.

Fijar el servidor donde se hace el slinktool. *server 232*.
```bash
    python checklist.py +dt 600 +server 232
```

### Ejemplo 4: checklist online (Ver estaciones por fuera en linea)
Filtrar online:*300*, redes: *CM*, estado: *offline* *recovering*
```bash
    python checklist.py +online 300 +net CM +status offline recovering
```

### Ejemplo 5: Agregar estaciones al checklist
Agregar estaciones a la RSNC
```bash
    python checklist.py +a RSNC
```

## Autores
- Emmanuel David Castillo ecastillo@sgc.gov.co

*creación: 2021/04/07*
 
*última actualización: 2021/04/07*
