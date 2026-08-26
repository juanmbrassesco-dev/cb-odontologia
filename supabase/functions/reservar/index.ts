// Portero de CB Odontología — endpoint POST /reservar
//
// EL PRIMERO QUE ESCRIBE. Los tres anteriores leen; éste anota una fila en
// `turnos`, y la anota A NOMBRE DE UNA PERSONA. De ahí salen las dos cosas que
// no hicieron falta hasta hoy: saber quién está pidiendo el turno, y que dos
// personas no puedan quedarse con la misma hora.
//
// 🔒 EXIGE SESIÓN INICIADA, igual que `/mis-pacientes`, y por eso tampoco lleva
// bloque en `config.toml`: la plataforma pide un JWT válido por defecto y acá
// no se lo apaga. El correo del paciente sale del token, NUNCA del cuerpo del
// pedido — si viniera en el cuerpo, cualquiera reservaría a nombre de
// cualquiera.
//
// LO QUE HACE, en orden:
//   1. mira quién es (el token)
//   2. revalida TODO lo que `GET /horarios-disponibles` ya había calculado,
//      reusando `_shared/disponibilidad.ts`
//   3. resuelve para quién es el turno (uno ya registrado, o uno nuevo)
//   4. inserta, y traduce el choque de la base a un 409
//
// 🔴 EL PASO 2 NO ES LA DEFENSA CONTRA LA DOBLE RESERVA, y conviene tenerlo
// claro para no borrarlo por "redundante": entre "miré que estaba libre" y "lo
// anoté" pasan milisegundos, y ahí entra el otro pedido. Lo único que impide de
// verdad el solapamiento es la restricción `turnos_sin_solapar` de la base. El
// paso 2 existe para contestar el MOTIVO correcto —"ese tratamiento no se
// reserva por la web"— en vez de un 409 que no explica nada.

import { withSupabase } from 'npm:@supabase/server@^1'

// Los tipos de la base entran por acá. No cambian NADA de lo que el endpoint
// hace: son para que TypeScript sepa qué columnas existen y avise en el editor
// cuando una consulta pide algo que no está.

import type { Database } from '../_shared/tipos-de-la-base.ts'

import {
  esFechaValida,
  esInstanteValido,
  diaSemanaISO,
  desfaseDeSantaFe,
  bloquesDelTramo,
  diaTapado,
  sumarMeses,
  fechaEnSantaFe,
  fueraDePlazo,
  unificarBloques,
  HORAS_DE_ANTICIPACION,
  MESES_DE_HORIZONTE,
} from '../_shared/disponibilidad.ts'

import { estadoDeLaPareja } from '../_shared/parejas.ts'

// Los avisos por correo. Van al final de todo y no pueden cambiar la
// respuesta: el detalle, abajo, donde se llaman.

import { enviarAvisos } from '../_shared/avisos.ts'

// El error que devuelve Postgres cuando la fila nueva se pisa con una que ya
// está. Es el código de "violación de exclusión", y en esta base sólo lo puede
// producir `turnos_sin_solapar`: no hay otra restricción de ese tipo.
//
// Se escribe con nombre y no suelto adentro del `if` porque un código de cinco
// caracteres no dice nada al que lo lee dentro de un año.
const CHOQUE_DE_TURNOS = '23P01'

// Topes de largo para lo que escribe una persona. No son reglas del
// consultorio: son el freno para que un pedido armado a mano no meta un texto
// de un megabyte en una columna que no tiene límite.
const LARGO_MAXIMO_NOMBRE = 60
const LARGO_MAXIMO_TELEFONO = 30
const LARGO_MAXIMO_DNI = 20
const LARGO_MAXIMO_OBSERVACIONES = 500

// Un pedido mal armado se contesta con el motivo: lo escribió quien está
// construyendo la pantalla y necesita saber qué corregir.
function pedidoInvalido( mensaje: string ): Response {

  return Response.json(
    { error: mensaje },
    { status: 400 },
  )
}

// Un fallo de la base se contesta SIN el detalle. El texto de Postgres nombra
// tablas, columnas y roles, y esto lo ve cualquiera.
function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo reservar el turno' },
    { status: 500 },
  )
}

// 🔒 LA RESPUESTA ÚNICA PARA LAS DOS FORMAS DE FALLAR CON `paciente_id`: que la
// fila no exista, y que exista pero sea de otro. Tienen que ser
// INDISTINGUIBLES —mismo número y mismo texto—, y el motivo es concreto: si se
// contestaran distinto, cualquiera con una sesión válida manda `paciente_id` 1,
// 2, 3… y el código de respuesta le va diciendo qué números existen. No ve los
// nombres, pero arma el mapa. Eso se llama ENUMERACIÓN (enumeration).
//
// Es el mismo patrón que `horarios-disponibles` ya usa con el profesional dado
// de baja, tratado igual que uno inexistente.
//
// Va en 403 y no en 404 porque acá hay sesión: la respuesta honesta es "estás
// identificado y esto no te corresponde". Un 404 afirmaría "eso no existe", que
// en la mitad de los casos es mentira.
function noEsTuyo(): Response {

  return Response.json(
    { error: 'Ese paciente no está disponible' },
    { status: 403 },
  )
}

// El choque: llegaste segundo. No es un error del pedido —estaba bien armado— y
// no es un error nuestro; es que el mundo cambió entre que miraste y anotaste.
function horaTomada(): Response {

  return Response.json(
    { error: 'Esa hora se acaba de ocupar. Elegí otra, por favor' },
    { status: 409 },
  )
}

// Un texto que escribió una persona, o `null` si no sirve.
//
// Las tres preguntas son distintas y las tres hacen falta: que sea un texto y
// no un número ni una lista disfrazada, que no esté vacío después de sacarle
// los espacios (' ' no es un apellido), y que no pase del tope.
function textoLimpio( valor: unknown, largoMaximo: number ): string | null {

  if ( typeof valor !== 'string' ) {
    return null
  }

  const limpio = valor.trim()

  if ( limpio.length === 0 ) {
    return null
  }

  if ( limpio.length > largoMaximo ) {
    return null
  }

  return limpio
}

export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( req, ctx ) => {

      if ( req.method !== 'POST' ) {
        return Response.json(
          { error: 'Este endpoint sólo acepta POST' },
          { status: 405 },
        )
      }

      // ── Quién pide ────────────────────────────────────────────────────────
      //
      // Mismo razonamiento que en `/mis-pacientes`: `userClaims` son los datos
      // de adentro del token, ya verificados por la librería contra las claves
      // del proyecto. No es lo que el cliente dice ser, es lo que el sistema de
      // cuentas firmó.
      const correo = ctx.userClaims?.email

      if ( !correo ) {
        return Response.json(
          { error: 'Sesión no válida' },
          { status: 403 },
        )
      }

      // ── El cuerpo del pedido ──────────────────────────────────────────────
      //
      // `req.json()` es la única línea del archivo que puede EXPLOTAR en vez de
      // devolver un error: si el cuerpo no es JSON, lanza. Por eso va adentro
      // de un `try`. Sin él, un cuerpo mal armado tumba la función entera y el
      // que llama recibe un 500 que no explica nada.
      let cuerpo: Record< string, unknown >

      try {
        cuerpo = await req.json()
      }
      catch {
        return pedidoInvalido( 'El cuerpo del pedido no es JSON válido' )
      }

      if ( !cuerpo || typeof cuerpo !== 'object' ) {
        return pedidoInvalido( 'El cuerpo del pedido tiene que ser un objeto' )
      }

      // ── Lo que se puede rechazar sin preguntarle nada a la base ───────────
      //
      // Se valida TODO del lado del servidor, incluso lo que la pantalla ya va
      // a validar. El navegador corre en la máquina del paciente y cualquiera
      // edita lo que manda: la validación del front es comodidad para el que la
      // usa bien, no una defensa.

      const profesionalId = Number( cuerpo.profesional )
      const tratamientoId = Number( cuerpo.tratamiento )

      if ( !Number.isInteger( profesionalId ) || !Number.isInteger( tratamientoId ) ) {
        return pedidoInvalido( 'profesional y tratamiento tienen que ser números' )
      }

      const inicio = cuerpo.inicio

      if ( typeof inicio !== 'string' || !esInstanteValido( inicio ) ) {
        return pedidoInvalido(
          'inicio va con fecha, hora y desfase: 2026-09-01T09:00:00-03:00',
        )
      }

      // Para quién es el turno. Son dos caminos y va EXACTAMENTE UNO: o el id
      // de un paciente ya registrado, o los datos de uno nuevo.
      //
      // La comparación de los dos `tiene…` entre sí cubre las dos formas de
      // equivocarse con una sola pregunta: si son iguales, o no vino ninguno o
      // vinieron los dos, y las dos cosas son un pedido ambiguo.
      const tienePacienteId = cuerpo.paciente_id !== undefined
      const tienePacienteNuevo = cuerpo.paciente_nuevo !== undefined

      if ( tienePacienteId === tienePacienteNuevo ) {
        return pedidoInvalido(
          'Mandá paciente_id o paciente_nuevo, uno de los dos',
        )
      }

      // ⚠ `observaciones` PUEDE TRAER DATOS DE SALUD. Se valida, se guarda, y
      // de acá en adelante no se vuelve a nombrar: no se devuelve en la
      // respuesta y no se escribe en ningún log.
      let observaciones: string | null = null

      if ( cuerpo.observaciones !== undefined ) {

        observaciones = textoLimpio( cuerpo.observaciones, LARGO_MAXIMO_OBSERVACIONES )

        if ( !observaciones ) {
          return pedidoInvalido(
            `Las observaciones tienen que ser un texto de hasta ${ LARGO_MAXIMO_OBSERVACIONES } caracteres`,
          )
        }
      }

      // ── Lo que hay que ir a preguntarle a la base ─────────────────────────

      const profesional = await ctx.supabaseAdmin
        .from( 'profesionales' )
        .select( 'id, activo, nombre, apellido, email' )
        .eq( 'id', profesionalId )
        .maybeSingle()

      if ( profesional.error ) {
        return falloDeBase()
      }

      // Un profesional dado de baja se contesta igual que uno inexistente, por
      // lo mismo de siempre: "existe pero no atiende más" es información del
      // consultorio.
      if ( !profesional.data || !profesional.data.activo ) {
        return pedidoInvalido( 'Ese profesional no está disponible' )
      }

      const tratamiento = await ctx.supabaseAdmin
        .from( 'tratamientos' )
        .select( 'id, duracion_web_min, nombre' )
        .eq( 'id', tratamientoId )
        .maybeSingle()

      if ( tratamiento.error ) {
        return falloDeBase()
      }

      if ( !tratamiento.data ) {
        return pedidoInvalido( 'Ese tratamiento no existe' )
      }

      // 🔴 LA DURACIÓN LA PONE LA BASE, NO EL CUERPO DEL PEDIDO. Si la mandara
      // el front, un pedido armado a mano pediría una limpieza de 60 minutos
      // declarando que dura 30, y el turno siguiente quedaría pisado (§ 6).
      //
      // Y `duracion_web_min` vacío significa "no se reserva por la web": lo
      // agenda el profesional después de la consulta previa. No es un error de
      // datos, es la regla del consultorio, y por eso es 400 y no 500.
      if ( !tratamiento.data.duracion_web_min ) {
        return pedidoInvalido( 'Ese tratamiento no se reserva por la web' )
      }

      const duracion = tratamiento.data.duracion_web_min

      // La consulta vive en `_shared/parejas.ts`: la hacen los dos endpoints y
      // la condición `activo` tiene que valer en los dos o no vale en ninguno.
      const pareja = await estadoDeLaPareja(
        ctx,
        profesionalId,
        tratamientoId,
      )

      if ( pareja === 'error-de-base' ) {
        return falloDeBase()
      }

      if ( pareja === 'no-la-hace' ) {
        return pedidoInvalido( 'Ese profesional no hace ese tratamiento' )
      }

      // ── La ventana de reserva ─────────────────────────────────────────────
      //
      // El reloj se mira UNA sola vez y el instante viaja de mano en mano, igual
      // que en `horarios-disponibles`: dos preguntas de la misma respuesta no
      // pueden quedar contestadas con relojes distintos.
      const ahora = new Date()

      const arranca = Date.parse( inicio )
      const fecha = fechaEnSantaFe( new Date( arranca ) )

      const ultimoDiaReservable = sumarMeses(
        fechaEnSantaFe( ahora ),
        MESES_DE_HORIZONTE,
      )

      if ( fecha > ultimoDiaReservable ) {
        return pedidoInvalido(
          `Todavía no se puede reservar tan lejos: el calendario llega hasta ${ MESES_DE_HORIZONTE } meses`,
        )
      }

      if ( fueraDePlazo( inicio, ahora ) ) {
        return pedidoInvalido(
          `Ese turno hay que sacarlo con ${ HORAS_DE_ANTICIPACION } horas de anticipación`,
        )
      }

      // ── ¿Ese bloque existe de verdad en la agenda de ese día? ─────────────
      //
      // No alcanza con que sea una hora en punto. Tiene que ser un bloque que
      // este profesional efectivamente ofrece ese día, y el tratamiento tiene
      // que entrar ahí adentro.

      const excepciones = await ctx.supabaseAdmin
        .from( 'excepciones' )
        .select( 'tipo, fecha_desde, fecha_hasta, semana_del_mes' )
        .eq( 'activa', true )
        .or( `profesional_id.is.null,profesional_id.eq.${ profesionalId }` )

      if ( excepciones.error ) {
        return falloDeBase()
      }

      if ( diaTapado( fecha, excepciones.data ) ) {
        return pedidoInvalido( 'Ese día el consultorio no atiende' )
      }

      const agenda = await ctx.supabaseAdmin
        .from( 'horarios_base' )
        .select( 'dia_semana, inicio, fin, fin_maximo' )
        .eq( 'profesional_id', profesionalId )
        .order( 'dia_semana' )
        .order( 'inicio' )

      if ( agenda.error ) {
        return falloDeBase()
      }

      const desfase = desfaseDeSantaFe( fecha )
      const dia = diaSemanaISO( fecha )

      const tramosDelDia = agenda.data.filter(
        ( tramo ) => tramo.dia_semana === dia,
      )

      const bloquesDelDia = unificarBloques(
        tramosDelDia.flatMap(
          ( tramo ) => bloquesDelTramo( fecha, tramo, duracion, desfase ),
        ),
      )

      // La comparación va por INSTANTE y no por texto, a propósito. El bloque
      // se arma con el desfase de Santa Fe ('-03:00') y el pedido podría venir
      // escrito en 'Z': son dos textos distintos para el mismo momento, y lo
      // que se compara es el momento.
      const bloque = bloquesDelDia.find(
        ( candidato ) => Date.parse( candidato.inicio ) === arranca,
      )

      if ( !bloque ) {
        return pedidoInvalido( 'Ese horario no está en la agenda de ese día' )
      }

      // `no_entra` viene decidido desde el tramo: el bloque existe, pero el
      // tratamiento no termina antes del cierre. Es el caso de la limpieza de
      // 60 minutos a las 16:30 un día que cierra a las 17:00.
      if ( bloque.estado === 'no_entra' ) {
        return pedidoInvalido( 'Ese tratamiento no entra en ese horario' )
      }

      // ── Para quién es el turno ────────────────────────────────────────────

      let pacienteId: number
      let pacienteNombre: string
      let pacienteApellido: string

      if ( tienePacienteId ) {

        const pedido = Number( cuerpo.paciente_id )

        if ( !Number.isInteger( pedido ) ) {
          return pedidoInvalido( 'paciente_id tiene que ser un número' )
        }

        // 🔒 LAS DOS CONDICIONES VAN EN LA MISMA CONSULTA, y eso ES la defensa
        // contra la enumeración. Preguntando primero "¿existe?" y después "¿es
        // tuyo?" habría dos respuestas distintas que distinguir; preguntando
        // las dos juntas, la fila aparece o no aparece, y el que pide no puede
        // saber cuál de las dos falló.
        const paciente = await ctx.supabaseAdmin
          .from( 'pacientes' )
          .select( 'id, nombre, apellido' )
          .eq( 'id', pedido )
          .eq( 'email', correo )
          .maybeSingle()

        if ( paciente.error ) {
          return falloDeBase()
        }

        if ( !paciente.data ) {
          return noEsTuyo()
        }

        pacienteId = paciente.data.id
        pacienteNombre = paciente.data.nombre
        pacienteApellido = paciente.data.apellido
      }
      else {

        const datos = cuerpo.paciente_nuevo

        if ( !datos || typeof datos !== 'object' ) {
          return pedidoInvalido( 'paciente_nuevo tiene que ser un objeto' )
        }

        const nuevo = datos as Record< string, unknown >

        const nombre = textoLimpio( nuevo.nombre, LARGO_MAXIMO_NOMBRE )
        const apellido = textoLimpio( nuevo.apellido, LARGO_MAXIMO_NOMBRE )

        if ( !nombre || !apellido ) {
          return pedidoInvalido( 'El paciente nuevo va con nombre y apellido' )
        }

        // Los tres opcionales. `undefined` significa "no lo mandaron" y se
        // guarda `null`; mandarlos mal sí es un error, porque el que llama
        // creyó que estaba cargando un dato que no se cargó.
        let telefono: string | null = null
        let dni: string | null = null
        let fechaNacimiento: string | null = null

        if ( nuevo.telefono !== undefined ) {

          telefono = textoLimpio( nuevo.telefono, LARGO_MAXIMO_TELEFONO )

          if ( !telefono ) {
            return pedidoInvalido( 'El teléfono no es válido' )
          }
        }

        if ( nuevo.dni !== undefined ) {

          dni = textoLimpio( nuevo.dni, LARGO_MAXIMO_DNI )

          if ( !dni ) {
            return pedidoInvalido( 'El DNI no es válido' )
          }
        }

        if ( nuevo.fecha_nacimiento !== undefined ) {

          if (
            typeof nuevo.fecha_nacimiento !== 'string'
            || !esFechaValida( nuevo.fecha_nacimiento )
          ) {
            return pedidoInvalido( 'La fecha de nacimiento va en formato AAAA-MM-DD' )
          }

          fechaNacimiento = nuevo.fecha_nacimiento
        }

        // 🔒 EL CORREO SALE DE LA SESIÓN, NO DEL CUERPO. Si el cuerpo pudiera
        // traerlo, cualquiera daría de alta un paciente bajo la casilla de otro
        // y después lo vería en su propia lista de `/mis-pacientes`.
        //
        // El alta va acá abajo y no antes a propósito: todo lo que se podía
        // rechazar ya se rechazó, así que un pedido inválido no deja una fila
        // de paciente colgada. Lo que SÍ puede pasar es que el turno choque con
        // otro (409) y el paciente quede creado igual — decidido el 23-ago-2026
        // con Juan: no se deduplica acá. La deduplicación vive en la mano de
        // Cecilia, con el buscador del panel ⑤ (9.7). El modo de falla de la
        // alternativa era peor: fundir en una sola fila a dos personas que
        // comparten casilla y nombre, y eso no falla con error.
        const alta = await ctx.supabaseAdmin
          .from( 'pacientes' )
          .insert( {
            nombre: nombre,
            apellido: apellido,
            email: correo,
            telefono: telefono,
            dni: dni,
            fecha_nacimiento: fechaNacimiento,
          } )
          .select( 'id' )
          .single()

        if ( alta.error ) {
          return falloDeBase()
        }

        pacienteId = alta.data.id
        pacienteNombre = nombre
        pacienteApellido = apellido
      }

      // ── La reserva ────────────────────────────────────────────────────────

      const turno = await ctx.supabaseAdmin
        .from( 'turnos' )
        .insert( {
          paciente_id: pacienteId,
          profesional_id: profesionalId,
          tratamiento_id: tratamientoId,
          inicio: inicio,
          duracion_min: duracion,
          canal: 'web',
          activo: true,
          observaciones_paciente: observaciones,
        } )
        .select( 'id, inicio, duracion_min' )
        .single()

      if ( turno.error ) {

        // 🔴 ACÁ ES DONDE LA BASE HACE DE ÁRBITRO. Los dos pedidos pasaron
        // todas las validaciones de arriba —los dos miraron y estaba libre—, y
        // el segundo se estrella contra `turnos_sin_solapar`. Ese choque no es
        // una falla del sistema: es el sistema funcionando.
        if ( turno.error.code === CHOQUE_DE_TURNOS ) {
          return horaTomada()
        }

        return falloDeBase()
      }

      // ── Los avisos ────────────────────────────────────────────────────────
      //
      // 🔴 LO QUE PASE ACÁ NO CAMBIA LA RESPUESTA. Se espera a que salgan —para
      // que un fallo se vea en el momento y no suelto media hora después—, pero
      // salgan o no, abajo se contesta 201: el turno YA está anotado. Si esto
      // devolviera 500, el paciente reservaría de nuevo y quedarían dos turnos
      // para la misma persona.
      //
      // `enviarAvisos` no lanza nunca, así que no lleva `try`: ya trae el suyo.
      // El segundo argumento —el MOTIVO— es lo que decide qué textos salen.
      // `_shared/avisos.ts` sabe escribir los de reserva y los de cancelación;
      // acá se le dice cuál de los dos. Sumado el 25-ago-2026, con ④.
      await enviarAvisos( {
        turnoId: turno.data.id,
        inicio: turno.data.inicio,
        duracionMin: turno.data.duracion_min,
        tratamiento: tratamiento.data.nombre,
        pacienteNombre: pacienteNombre,
        pacienteApellido: pacienteApellido,
        pacienteCorreo: correo,
        profesionalNombre: profesional.data.nombre,
        profesionalApellido: profesional.data.apellido,
        profesionalCorreo: profesional.data.email,
        tieneObservaciones: observaciones !== null,
      },
      'reserva' )

      // Lo mínimo, y nada de lo que entró por el cuerpo: ni el nombre del
      // paciente ni las observaciones vuelven.
      return Response.json(
        {
          id: turno.data.id,
          inicio: turno.data.inicio,
          duracion_min: turno.data.duracion_min,
          profesional: profesionalId,
          tratamiento: tratamientoId,
        },
        { status: 201 },
      )
    },
  ),

}
