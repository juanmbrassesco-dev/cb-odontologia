-- LA BATERÍA DE LA BASE — todo lo que la base tiene que hacer para la repesca.
--
-- Corre ADENTRO de `begin … rollback`: crea sus pacientes y sus turnos, los usa
-- y los deshace. La base queda como estaba, y por eso se puede correr sobre la
-- base real sin miedo.
--
-- 🔴 LO QUE LA HACE DISTINTA DE MIRAR DESDE EL PANEL: cada permiso se prueba
-- CON `set local role service_role` PUESTO, o sea como el portero y no como
-- dueño de la base. El dueño atraviesa cualquier permiso, así que probar desde
-- arriba da verde SIEMPRE. Esta batería nació el 28-ago-2026 justamente porque
-- once escenarios en verde como dueño escondían un `42501` que aparecía al
-- primer llamado real.
--
-- CÓMO SE CORRE, parado en la raíz del repo:
--
--   supabase db query --linked -f pruebas/probar-repesca.sql
--
-- Cada fila dice qué se esperaba y qué salió. `veredicto` OK o FALLA.

begin;

create temporary table resultados (
  orden    int,
  caso     text,
  obtenido text,
  esperado text
) on commit drop;

create temporary table ids (
  turno   bigint,
  paciente bigint
) on commit drop;


-- ── El escenario base ────────────────────────────────────────────────────────

insert into public.pacientes ( nombre, apellido, email )
  values ( 'Ana', 'Bateria', 'bateria-repesca@ejemplo.test' );

insert into public.turnos (
    paciente_id, profesional_id, tratamiento_id, motivo_consulta_id,
    inicio, duracion_min, canal, activo, aviso_estado, observaciones_paciente
  )
  values (
    ( select id from public.pacientes where email = 'bateria-repesca@ejemplo.test' ),
    1,
    ( select id from public.tratamientos where nombre = 'consulta' ),
    ( select id from public.tratamientos where nombre = 'limpieza' ),
    now() + interval '50 hours', 30, 'manual', true, null,
    'me duele una muela'
  );

insert into ids
  select ( select id from public.turnos
            where paciente_id = ( select id from public.pacientes where email = 'bateria-repesca@ejemplo.test' ) ),
         ( select id from public.pacientes where email = 'bateria-repesca@ejemplo.test' );


-- ═══ A · QUÉ PUEDE ESCRIBIR EL PORTERO EN `turnos` ═══════════════════════════

do $$
declare
  r text;
  t bigint := ( select turno from ids );
begin

  -- A1 · las tres columnas del grant
  set local role service_role;
  begin
    update public.turnos set aviso_estado = 'enviando', aviso_at = now(), activo = true where id = t;
    r := 'pasa';
  exception when insufficient_privilege then r := 'rebota 42501';
  end;
  reset role;
  insert into resultados values ( 1, 'A1 · el portero escribe activo + aviso_estado + aviso_at', r, 'pasa' );

  -- A2 · una columna que NO está en el grant
  set local role service_role;
  begin
    update public.turnos set nota = 'no deberia poder' where id = t;
    r := 'pasa';
  exception when insufficient_privilege then r := 'rebota 42501';
  end;
  reset role;
  insert into resultados values ( 2, 'A2 · el portero NO escribe nota', r, 'rebota 42501' );

  -- A3 · borrar
  set local role service_role;
  begin
    delete from public.turnos where id = t;
    r := 'pasa';
  exception when insufficient_privilege then r := 'rebota 42501';
  end;
  reset role;
  insert into resultados values ( 3, 'A3 · el portero NO borra turnos', r, 'rebota 42501' );

  -- A4 · leer pacientes
  set local role service_role;
  begin
    perform 1 from public.pacientes limit 1;
    r := 'pasa';
  exception when insufficient_privilege then r := 'rebota 42501';
  end;
  reset role;
  insert into resultados values ( 4, 'A4 · el portero LEE pacientes', r, 'pasa' );

  -- A5 · escribir pacientes
  set local role service_role;
  begin
    update public.pacientes set nombre = 'Pisado' where id = ( select paciente from ids );
    r := 'pasa';
  exception when insufficient_privilege then r := 'rebota 42501';
  end;
  reset role;
  insert into resultados values ( 5, 'A5 · el portero NO escribe pacientes', r, 'rebota 42501' );

  -- A6 · el check del aviso
  set local role service_role;
  begin
    update public.turnos set aviso_estado = 'Reservado' where id = t;
    r := 'pasa';
  exception when check_violation then r := 'rebota 23514';
  end;
  reset role;
  insert into resultados values ( 6, 'A6 · el check rechaza Reservado con mayuscula', r, 'rebota 23514' );

  -- A7 · el RPC, ejecutado por quien NO debe
  set local role anon;
  begin
    perform public.reclamar_avisos_pendientes( 1 );
    r := 'pasa';
  exception when insufficient_privilege then r := 'rebota 42501';
  end;
  reset role;
  insert into resultados values ( 7, 'A7 · anon NO ejecuta el RPC', r, 'rebota 42501' );

end $$;


-- ═══ B · EL TRIGGER QUE BORRA LA MARCA ═══════════════════════════════════════

do $$
declare
  t bigint := ( select turno from ids );
  otro bigint;
  marca text;
begin

  insert into public.profesionales ( nombre, apellido, email, activo )
    values ( 'Segundo', 'Bateria', 'segundo-bateria@ejemplo.test', true )
    returning id into otro;

  -- B1 a B5 · las cinco columnas que el correo nombra
  update public.turnos set aviso_estado = 'reservado' where id = t;
  update public.turnos set inicio = inicio + interval '1 hour' where id = t;
  select aviso_estado into marca from public.turnos where id = t;
  insert into resultados values ( 11, 'B1 · mover la hora borra la marca', coalesce( marca, '(vacio)' ), '(vacio)' );

  update public.turnos set aviso_estado = 'reservado' where id = t;
  update public.turnos set duracion_min = 60 where id = t;
  select aviso_estado into marca from public.turnos where id = t;
  insert into resultados values ( 12, 'B2 · cambiar la duracion borra la marca', coalesce( marca, '(vacio)' ), '(vacio)' );

  update public.turnos set aviso_estado = 'reservado' where id = t;
  update public.turnos set profesional_id = otro where id = t;
  select aviso_estado into marca from public.turnos where id = t;
  insert into resultados values ( 13, 'B3 · reasignar a otro profesional borra la marca', coalesce( marca, '(vacio)' ), '(vacio)' );

  update public.turnos set aviso_estado = 'reservado' where id = t;
  update public.turnos set tratamiento_id = ( select id from public.tratamientos where nombre = 'limpieza' ) where id = t;
  select aviso_estado into marca from public.turnos where id = t;
  insert into resultados values ( 14, 'B4 · cambiar el tratamiento borra la marca', coalesce( marca, '(vacio)' ), '(vacio)' );

  update public.turnos set tratamiento_id = null, aviso_estado = 'reservado' where id = t;
  update public.turnos set tratamiento_id = ( select id from public.tratamientos where nombre = 'consulta' ) where id = t;
  select aviso_estado into marca from public.turnos where id = t;
  insert into resultados values ( 15, 'B5 · de tratamiento VACIO a cargado borra la marca', coalesce( marca, '(vacio)' ), '(vacio)' );

  -- B6 · el control: una columna que el correo NO nombra
  update public.turnos set aviso_estado = 'reservado' where id = t;
  update public.turnos set nota = 'esto no le cambia nada al paciente' where id = t;
  select aviso_estado into marca from public.turnos where id = t;
  insert into resultados values ( 16, 'B6 · CONTROL: tocar la nota NO borra la marca', coalesce( marca, '(vacio)' ), 'reservado' );

  -- B7 · escribir sólo la marca no se dispara a sí mismo
  update public.turnos set aviso_estado = 'enviando', aviso_at = now() where id = t;
  select aviso_estado into marca from public.turnos where id = t;
  insert into resultados values ( 17, 'B7 · escribir la marca NO se borra a si misma', coalesce( marca, '(vacio)' ), 'enviando' );

  -- deja el turno listo para la parte C
  update public.turnos
     set profesional_id = 1,
         duracion_min   = 30,
         aviso_estado   = null,
         aviso_at       = null,
         nota           = null
   where id = t;

  delete from public.profesionales where id = otro;

end $$;


-- ═══ C · EL RECLAMO, LLAMADO COMO EL PORTERO ═════════════════════════════════

create temporary table casos ( caso text, esperado text, turno bigint ) on commit drop;

insert into public.pacientes ( nombre, apellido, email )
  values ( 'Sin', 'Correo', null );

insert into public.turnos ( paciente_id, profesional_id, inicio, duracion_min, canal, activo, aviso_estado, aviso_at )
select ( select paciente from ids ),
       1,
       now() + ( c.hora || ' hours' )::interval,
       30, 'manual', c.activo, c.marca,
       case when c.viejo then now() - interval '20 minutes' else now() end
  from ( values
      (  61, true , 'enviando'   , false ),
      (  62, true , 'enviando'   , true  ),
      (  63, true , 'reservado'  , false ),
      (  64, true , 'cancelado'  , false ),
      (  65, false, null         , false ),
      (  66, false, 'enviando'   , false ),
      (  67, false, 'enviando'   , true  ),
      (  68, false, 'reservado'  , false ),
      (  69, false, 'cancelado'  , false )
    ) as c ( hora, activo, marca, viejo );

insert into public.turnos ( paciente_id, profesional_id, inicio, duracion_min, canal, activo, aviso_estado )
  values ( ( select id from public.pacientes where apellido = 'Correo' and email is null ),
           1, now() + interval '70 hours', 30, 'manual', true, null );

insert into casos ( caso, esperado, turno )
select x.caso, x.esperado, t.id
  from ( values
      ( 'C2a · activo + enviando reciente'      , 'no vuelve' , 61 ),
      ( 'C2b · activo + enviando trabado'       , 'VUELVE'    , 62 ),
      ( 'C3  · activo + reservado'              , 'no vuelve' , 63 ),
      ( 'C4  · activo + cancelado (reactivado)' , 'VUELVE'    , 64 ),
      ( 'C5  · apagado + vacio'                 , 'no vuelve' , 65 ),
      ( 'C6a · apagado + enviando reciente'     , 'no vuelve' , 66 ),
      ( 'C6b · apagado + enviando trabado'      , 'VUELVE'    , 67 ),
      ( 'C7  · apagado + reservado'             , 'VUELVE'    , 68 ),
      ( 'C8  · apagado + cancelado'             , 'no vuelve' , 69 ),
      ( 'C9  · paciente SIN correo'             , 'no vuelve' , 70 )
    ) as x ( caso, esperado, hora )
  join public.turnos t
    on t.inicio = now() + ( x.hora || ' hours' )::interval;

insert into casos values ( 'C1  · activo + vacio', 'VUELVE', ( select turno from ids ) );


set local role service_role;

create temporary table vueltos on commit drop as
  select * from public.reclamar_avisos_pendientes( 50 );

-- Una segunda corrida INMEDIATA no se puede llevar lo mismo: acaba de quedar
-- en 'enviando' y todavía no pasaron diez minutos.
create temporary table segunda on commit drop as
  select turno_id from public.reclamar_avisos_pendientes( 50 );

reset role;

insert into resultados
select 20 + row_number() over ( order by c.caso ),
       c.caso,
       case when v.turno_id is null then 'no vuelve' else 'VUELVE' end,
       c.esperado
  from casos c
  left join vueltos v on v.turno_id = c.turno;

insert into resultados
select 40, 'C10 · la segunda corrida no repite ninguno', count(*)::text, '0'
  from segunda;

insert into resultados
select 41, 'C11 · el reclamo dejo la marca en enviando', count(*)::text, ( select count(*)::text from vueltos )
  from public.turnos t
  join vueltos v on v.turno_id = t.id
 where t.aviso_estado = 'enviando'
   and t.aviso_at is not null;

insert into resultados
select 42, 'C12 · el correo viene con todos los datos',
       case when v.paciente_email is not null
             and v.profesional_email is not null
             and v.tratamiento_nombre is not null
             and v.motivo_nombre is not null
             and v.tiene_observaciones
            then 'completo' else 'FALTAN DATOS' end,
       'completo'
  from vueltos v
 where v.turno_id = ( select turno from ids );


-- ═══ D · EL MARCADO CONDICIONADO ═════════════════════════════════════════════

do $$
declare
  t bigint := ( select turno from ids );
  tocadas int;
begin

  set local role service_role;

  update public.turnos set aviso_estado = 'reservado', aviso_at = now()
   where id = t and aviso_estado = 'enviando';
  get diagnostics tocadas = row_count;

  reset role;
  insert into resultados values ( 50, 'D1 · marcar mientras dice enviando escribe', tocadas::text, '1' );

  -- Ahora la marca ya NO dice 'enviando': el mismo update no tiene que pisar nada.
  set local role service_role;

  update public.turnos set aviso_estado = 'cancelado', aviso_at = now()
   where id = t and aviso_estado = 'enviando';
  get diagnostics tocadas = row_count;

  reset role;
  insert into resultados values ( 51, 'D2 · si la marca ya cambio, el marcado no pisa', tocadas::text, '0' );

end $$;


-- ═══ E · REGRESIONES DE LAS FASES ANTERIORES ═════════════════════════════════

do $$
declare
  r text;
  p bigint := ( select paciente from ids );
begin

  -- E1 · el check del canal
  begin
    insert into public.turnos ( paciente_id, profesional_id, inicio, duracion_min, canal )
      values ( p, 1, now() + interval '80 hours', 30, 'Web' );
    r := 'pasa';
  exception when check_violation then r := 'rebota 23514';
  end;
  insert into resultados values ( 60, 'E1 · el check del canal rechaza Web con mayuscula', r, 'rebota 23514' );

  -- E2 · el límite de dos turnos web por profesional
  insert into public.turnos ( paciente_id, profesional_id, inicio, duracion_min, canal )
    values ( p, 1, now() + interval '81 hours', 30, 'web' ),
           ( p, 1, now() + interval '82 hours', 30, 'web' );

  begin
    insert into public.turnos ( paciente_id, profesional_id, inicio, duracion_min, canal )
      values ( p, 1, now() + interval '83 hours', 30, 'web' );
    r := 'pasa';
  exception when others then r := 'rebota ' || sqlstate;
  end;
  insert into resultados values ( 61, 'E2 · el tercer turno web con el mismo profesional rebota', r, 'rebota CB001' );

  -- E3 · el mismo tercer turno, pero cargado a mano, SÍ entra
  begin
    insert into public.turnos ( paciente_id, profesional_id, inicio, duracion_min, canal )
      values ( p, 1, now() + interval '84 hours', 30, 'manual' );
    r := 'pasa';
  exception when others then r := 'rebota ' || sqlstate;
  end;
  insert into resultados values ( 62, 'E3 · el tope NO alcanza al consultorio', r, 'pasa' );

end $$;


-- ── El resultado ─────────────────────────────────────────────────────────────

select caso,
       obtenido,
       esperado,
       case when obtenido = esperado then 'OK' else 'FALLA' end as veredicto
  from resultados
 order by orden;

rollback;
