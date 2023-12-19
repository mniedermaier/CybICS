PROGRAM cybICS
  VAR
    (* heartbeat LED on the PCB *)
    heartbeat AT %QX0.0 : BOOL;
    compressor AT %QX0.1 : BOOL;
  END_VAR
  VAR
    (* Counter LED heartbeat *)
    countHeartbeat : UINT := 0;  
  END_VAR

  IF countHeartbeat < 20 THEN 
    heartbeat := FALSE;
    
  ELSIF countHeartbeat < 40 THEN
    heartbeat := TRUE;
  ELSE
    countHeartbeat := 0;
  END_IF;
  
  compressor := TRUE;

  (* Increase the counters *)
  countHeartbeat := countHeartbeat + 1;
END_PROGRAM


CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK TaskMain(INTERVAL := T#50ms,PRIORITY := 0);
    PROGRAM Inst0 WITH TaskMain : cybICS;
  END_RESOURCE
END_CONFIGURATION

