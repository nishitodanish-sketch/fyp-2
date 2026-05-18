C Copyright(c) 1997, Space Science and Engineering Center, UW-Madison
C Refer to "McIDAS Software Acquisition and Distribution Policies"
C in the file  mcidas/data/license.txt

C *** $Id: areacom.inc,v 1.6 1997/10/10 20:16:10 dglo Exp $ ***

C  Area-related shared data

C  You must include 'araparm.inc' before including this file

      INTEGER	NAREA
      INTEGER	AREAS(MAXOPENAREAS)
      INTEGER	NEL(MAXOPENAREAS)
      INTEGER	NOFF(MAXOPENAREAS)
      INTEGER	MAXSIZ(MAXOPENAREAS)
      INTEGER	ARADIR(64,MAXOPENAREAS)
      INTEGER	NCALB(4,MAXOPENAREAS)
      INTEGER	OPTION(NUMAREAOPTIONS,MAXOPENAREAS)
      INTEGER	FLIP(MAXOPENAREAS)
      COMMON/ARACOM/NAREA,AREAS,NEL,NOFF,MAXSIZ,ARADIR,NCALB,
     >   OPTION,FLIP

C  The following common block was formerly called 'PREFIX', but
C  had to be changed because this conflicted with an external
C  symbol also named 'PREFIX' in the SPICE library from JPL.

      INTEGER	PAREA(MAXOPENAREAS)
      INTEGER	PLINE(MAXOPENAREAS)
      INTEGER	PRFX(250,MAXOPENAREAS)
      COMMON/ARAPFX/PAREA,PLINE,PRFX

      INTEGER	IAR(MAXOPENAREAS)
      INTEGER	NTR(MAXOPENAREAS)
      INTEGER	IMOD(MAXOPENAREAS)
      INTEGER	JBUF(4767,MAXOPENAREAS)
      COMMON/WRACK/IAR,NTR,IMOD,JBUF
