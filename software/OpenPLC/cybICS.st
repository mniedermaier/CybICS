PROGRAM cybICS
  VAR
    (* heartbeat LED on the PCB *)
    systemSen AT %IX0.1 : BOOL;
    boSen AT %IX0.2 : BOOL;
    heartbeat AT %QX0.0 : BOOL;
    compressor AT %QX0.1 : BOOL;
    systemValve AT %QX0.2 : BOOL;
    gstSig AT %QX0.3 : BOOL;
    gst AT %MW100 : UINT := 0;
    hpt AT %MW102 : UINT := 0;
    stop AT %MW104 : UINT := 0;
    manual AT %MW106 : UINT := 0;
    
    compressorState AT %MW200 : UINT;
    gstState AT %MW202 : UINT;
  END_VAR
  VAR
    (* Counter LED heartbeat *)
    countHeartbeat : UINT := 0;  
  END_VAR

  (* System heartbeat *)
  IF countHeartbeat < 20 THEN 
    heartbeat := FALSE;    
  ELSIF countHeartbeat < 40 THEN
    heartbeat := TRUE;
  ELSE
    countHeartbeat := 0;
  END_IF;
  
  (* System running state *)
  IF stop < 1 THEN
    (* System running in automatic mode *)
    IF manual < 1 THEN
      (* Refill GST, when below 60 and fill it up to 254 *)
      IF gst < 60 AND gstState = 0 THEN
        gstState := 1;
      ELSIF gst < 255 AND gstState = 1 THEN
        gstState := 1;
      ELSE
        gstState := 0;
      END_IF;      

      (* Run compressor when below 60 and fill it up to 89 *)
      (* Only run compressor, when GST > 50 *)
      IF hpt < 60 AND compressorState = 0 AND gst > 50 THEN    
        compressorState := 1;
      ELSIF hpt < 90 AND compressorState = 1 AND gst > 50 THEN    
        compressorState := 1;
      ELSE
        compressorState := 0;
      END_IF;
  
  
      IF hpt > 50 AND hpt<100 THEN
        systemValve := TRUE;
      ELSE
        systemValve := FALSE;
      END_IF;
  
      IF compressorState = 1 THEN
        compressor := TRUE;
      ELSE
        compressor := FALSE;
      END_IF;

      IF gstState = 1 THEN
        gstSig := TRUE;
      ELSE
        gstSig := FALSE;
      END_IF;
      (* ELSE System running in manual mode *)  
    END_IF;
  (* System stop state *)
  ELSE
    compressorState := 0;
    compressor := FALSE;
    systemValve := FALSE;
    gstState := 0;
    gstSig := FALSE;
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

