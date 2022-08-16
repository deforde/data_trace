TARGET_EXEC := data_trace

BUILD_DIR := build
SRC_DIRS := src

SRCS := $(shell find $(SRC_DIRS) -name '*.c')
OBJS := $(SRCS:%=$(BUILD_DIR)/%.o)
DEPS := $(OBJS:.o=.d)

INC_DIRS := $(shell find $(SRC_DIRS) -type d)
INC_FLAGS := $(addprefix -I,$(INC_DIRS))

CFLAGS := -Wall -Wextra -Wpedantic -Werror -Wno-unused-but-set-variable $(INC_FLAGS) -MMD -MP
LDFLAGS := -lm

EXECUTABLE := $(BUILD_DIR)/$(TARGET_EXEC)
GDB_CMDS_FILE := ./gdb_cmds

all: CFLAGS += -O3
all: executable

debug: CFLAGS += -g3 -D_FORTIFY_SOURCE=2
debug: executable

san: debug
san: CFLAGS += -fsanitize=address,undefined
san: LDFLAGS += -fsanitize=address,undefined

executable: $(EXECUTABLE)

$(EXECUTABLE): $(OBJS)
	$(CC) $(OBJS) -o $@ $(LDFLAGS)

$(BUILD_DIR)/%.c.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

.PHONY: clean compdb valgrind run

clean:
	@rm -rf $(BUILD_DIR)


compdb: clean
	@bear -- $(MAKE) san && \
	 mv compile_commands.json build

valgrind: debug
	@valgrind ./$(EXECUTABLE)

test: debug
	@gdb -x $(GDB_CMDS_FILE) ./$(EXECUTABLE)

-include $(DEPS)
