PROGRAM cybICS
  VAR
    (* STM32 reset *)
    stm32reset AT %QX0.0 : BOOL;
    (* heartbeat LED on the PCB *)
    heartbeat AT %QX0.1 : BOOL;
  END_VAR
  VAR
    (* initialize stm32 *)
    initialize : UINT := 0;  
    (* Counter between processes *)
    countHeartbeat : UINT := 0;  
  END_VAR

  IF initialize < 10 THEN
    stm32reset := FALSE;
    initialize := initialize + 1;
  ELSE
    stm32reset := TRUE;


    IF countHeartbeat < 20 THEN 
      heartbeat := FALSE;
    ELSIF countHeartbeat < 40 THEN
      heartbeat := TRUE;
    ELSE
      countHeartbeat := 0;
    END_IF;

    (* Increase the counters *)
    countHeartbeat := countHeartbeat + 1;
  END_IF;
END_PROGRAM


CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK TaskMain(INTERVAL := T#50ms,PRIORITY := 0);
    PROGRAM Inst0 WITH TaskMain : cybICS;
  END_RESOURCE
END_CONFIGURATION

