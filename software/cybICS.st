PROGRAM cybICS
  VAR
    (* heartbeat LED on the PCB *)
    heartbeat AT %QX0.0 : BOOL;
    compressor AT %QX0.1 : BOOL;
    gst AT %MW100 : UINT;
    hpt AT %MW101 : UINT;
    
    compressorState AT %MW200 : UINT;
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
  
  IF hpt < 60 AND compressorState = 0 THEN    
    compressorState := 1;
  ELSIF hpt < 140 AND compressorState = 1 THEN    
    compressorState := 1;
  ELSE
    compressorState := 0;
  END_IF;
  
  IF compressorState = 1 THEN
    compressor := TRUE;
  ELSE
    compressor := FALSE;
  END_IF;
  
  (* Increase the counters *)
  countHeartbeat := countHeartbeat + 1;
END_PROGRAM


CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK TaskMain(INTERVAL := T#50ms,PRIORITY := 0);
    PROGRAM Inst0 WITH TaskMain : cybICS;
  END_RESOURCE
END_CONFIGURATION

