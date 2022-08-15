set logging overwrite on
set logging redirect on
set logging enabled on
watch y
command
silent
printf "y=%f\n",y
cont
end
run
quit
