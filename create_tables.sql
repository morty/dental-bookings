drop table if exists patients;
drop table if exists referrals;
drop table if exists appointments;
drop table if exists char_codes;

 
create table patients (
	id serial not null primary key,
	first_name varchar (255),
	last_name varchar (255),
	nhs_number varchar (20),
	date_of_birth date,
	tel_no varchar (20),
	urgency varchar(20)
);

create table referrals (
	id serial not null primary key,
	uuid varchar(100) not null,
	patient_id integer not null,
	allergies text,
	medical_history text,
	bleeding_disorders text,
	medications text,
	treatment_requested text, 	/*  List of teeth, coded as UL, UR, LL, LR followed by A-E */
	parents_aware_flag varchar(100),
	problem_teeth varchar (255),
	referral_date date not null
);

create table appointments (
	id serial not null primary key,
	patient_id integer not null,
	appointment_date date,
	time_of_day char (4)	/*  am or pm */
);

create table char_codes (
	domain char(4) primary key,
	char_code char(4),
	description varchar (20)
);

insert into char_codes values ('DOM', 'TH', 'Tooth');
insert into char_codes values ('TH', 'ULA', 'Upper-Left A');
/* etc */

