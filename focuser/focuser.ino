#include "Arduino.h"

static const uint32_t COMMAND_MAX_LENGTH = 20;
static const uint32_t COMMAND_NAME_LENGTH = 8;
static const uint32_t SERIAL_BAUDRATE = 115200;
static const uint32_t MAX_INDEX = 2;
static const uint32_t NAME_LENGTH = 20;

static const int32_t MAX_INCREMENT = 100;
static const int32_t MAX_STEPS = 10000;

char command_string[COMMAND_MAX_LENGTH];
char command_name[COMMAND_NAME_LENGTH];

typedef int32_t Result_t;

static const Result_t SUCCESS = 1;
static const Result_t INDEX_UNDER_ZERO = 2;
static const Result_t INDEX_OVER_MAX = 3;

class FocuserInfo{
public:
  FocuserInfo() : 
    _current_position(0),
    _set_position(0)
  {}
  int32_t GetPosition() const { return _current_position; }
  bool IsMoving() const { return _current_position != _set_position; }
  void Halt(){ _set_position = _current_position; }
  void RequestMove(int32_t increment){
    int32_t trimmed = max(-MAX_INCREMENT, min(MAX_INCREMENT, increment));
    int32_t desired = max(-MAX_STEPS, min(MAX_STEPS, _set_position + trimmed));
    _set_position = desired;    
  }
  int32_t GetDirection() const { 
    return _current_position < _set_position ? 1 : -1;
  }
  void PerformMove(int32_t movement){
    _current_position += movement;
  }
private:
  int32_t _current_position;
  int32_t _set_position;
};

FocuserInfo focusers[MAX_INDEX] = {
  FocuserInfo(), 
  FocuserInfo()
};

void StepStepper(FocuserInfo& info, int32_t dir){
  // TODO!
}

void RunFocusers(){
  for (uint32_t i=0; i<MAX_INDEX; ++i){
    FocuserInfo& focuser = focusers[i];
    if (focuser.IsMoving()){
      int32_t dir = focuser.GetDirection();
      StepStepper(focuser, dir);
      focuser.PerformMove(dir);
    }
  }
}

Result_t CheckIndex(int32_t focuser_index){
  if (focuser_index < 0){
    return INDEX_UNDER_ZERO;
  }
  if (focuser_index >= MAX_INDEX){
    return INDEX_OVER_MAX;
  }
  return SUCCESS;
}

#define VALIDATE_INDEX(index)\
do { \
  Result_t result = CheckIndex(index); \
  if (result != SUCCESS){ \
    return result; \
  } \
} while(0) 

#define PRINT_RESULT_OR_ERROR_TO_SERIAL(x, v)\
do { \
  Result_t result = (x); \
  if (result == SUCCESS){ \
    Serial.println(v); \
  } else{ \
    Serial.print("ERROR: "); \
    Serial.println(result); \
  } \
} while(0) 


Result_t GetName(int32_t focuser_index, char my_name[NAME_LENGTH]){
  VALIDATE_INDEX(focuser_index);
  snprintf(my_name, "Focuser%d", focuser_index);
  return SUCCESS;
}

Result_t IsFocuserMoving(int32_t focuser_index, bool* is_moving){
  VALIDATE_INDEX(focuser_index);
  *is_moving = focusers[focuser_index].IsMoving();
  return SUCCESS;
}

Result_t GetPosition(int32_t focuser_index, int32_t* result){
  VALIDATE_INDEX(focuser_index);
  *result = focusers[focuser_index].GetPosition();
  return SUCCESS;
}

Result_t GetTemperature(int32_t focuser_index, int32_t* result){
  VALIDATE_INDEX(focuser_index);
  *result = 0;
  // TODO!
  return SUCCESS;
}

Result_t HaltFocuser(int32_t focuser_index){
  VALIDATE_INDEX(focuser_index);
  focusers[focuser_index].Halt();
  return SUCCESS;
}
  
Result_t MoveFocuser(int32_t focuser_index, int32_t increment){
  VALIDATE_INDEX(focuser_index);
  focusers[focuser_index].RequestMove(increment);
  return SUCCESS;
}

void ReadSerial(){
  if (Serial.available()){
    memset(command_string, 0, COMMAND_MAX_LENGTH);
    memset(command_name, 0, COMMAND_NAME_LENGTH);
    int32_t focuser_index = 0;
    int32_t command_argument = 0;
    
    Serial.readBytesUntil('\n', command_string, COMMAND_MAX_LENGTH-1);
    sscanf(command_string, "%s %ld %ld", command_name, &focuser_index, &command_argument);

    if (strcmp("GET_NAME" ,command_name) == 0){
      char my_name[NAME_LENGTH] = {0};
      PRINT_RESULT_OR_ERROR_TO_SERIAL(GetName(focuser_index, my_name), my_name);
    }  
    else if (strcmp("IS_MOVING", command_name) == 0){
      bool is_moving = true;
      PRINT_RESULT_OR_ERROR_TO_SERIAL(IsFocuserMoving(focuser_index, &is_moving), (is_moving ? "True" : "False"));
    }
    else if (strcmp("GET_POSITION", command_name) == 0){
      int32_t position_value = 0;
      PRINT_RESULT_OR_ERROR_TO_SERIAL(GetPosition(focuser_index, &position_value), position_value);
    }
    else if (strcmp("GET_TEMP" ,command_name) == 0){
      int32_t temperature_value = 0;
      PRINT_RESULT_OR_ERROR_TO_SERIAL(GetTemperature(focuser_index, &temperature_value), temperature_value);
    }  
    else if (strcmp("HALT" ,command_name) == 0){
      PRINT_RESULT_OR_ERROR_TO_SERIAL(HaltFocuser(focuser_index), "OK");
    }  
    else if (strcmp("MOVE" ,command_name) == 0){
      PRINT_RESULT_OR_ERROR_TO_SERIAL(MoveFocuser(focuser_index, command_argument), "OK");
    }
    else if (strcmp("IS_ALIVE" ,command_name) == 0){
      PRINT_RESULT_OR_ERROR_TO_SERIAL(CheckIndex(focuser_index), "OK");
    }
    else {
      Serial.print("ERROR: Unknown command send:");
      Serial.println(command_string);
    }
  }
}

void setup() {
    Serial.begin(SERIAL_BAUDRATE);
}

void loop() {
  ReadSerial();
  RunFocusers();
}
