C Copyright(c) 1997, Space Science and Engineering Center, UW-Madison
C Refer to "McIDAS Software Acquisition and Distribution Policies"
C in the file  mcidas/data/license.txt

C *** $Id: clsara.f,v 1.12 1997/10/10 20:16:42 dglo Exp $ ***

*$ Name:
*$      clsara - Closes a McIDAS area.
*$
*$ Interface:
*$      subroutine
*$      clsara(integer area)
*$
*$ Input:
*$      area    - Number of MCIDAS area to be closed.
*$
*$ Input and Output:
*$      none
*$
*$ Output:
*$      none
*$
*$ Return values:
*$      none
*$
*$ Remarks:
*$      After calling this routine the only area access routine that
*$      will work is opnara().
*$
*$ Categories:
*$      image
*$      file

      SUBROUTINE CLSARA(AREA)
      IMPLICIT NONE
      INTEGER AREA

      ! local variables

      INTEGER I
      INTEGER JB

      ! symbolic constants & shared data

      INCLUDE 'areaparm.inc'
      INCLUDE 'areacom.inc'

C --- CHECK IF ANY AREAS ARE OPEN
      IF(NAREA.EQ.0) RETURN

C --- CHECK IF AREA IS OPEN
      DO 10 I=1,NAREA
        IF(AREA.EQ.AREAS(I))GOTO 20
10    CONTINUE
      RETURN

C --- CHECK IF AREA NEEDS THE BINDOFF
20    CONTINUE
      IF(AREA.EQ.IAR(I).AND.IMOD(I).EQ.1) THEN
         CALL WRTRKA(IAR(I))
         IMOD(I)=0
      ENDIF

C --- ELIMINATE THE AREA FROM THE COMMON
      IF(I.NE.NAREA) THEN
         DO 30 JB=I,NAREA-1

C --- RESET ARACOM
           AREAS(JB)=AREAS(JB+1)
           NEL(JB)=NEL(JB+1)
           NOFF(JB) = NOFF(JB+1)
           MAXSIZ(JB) = MAXSIZ(JB+1)
           CALL MOVW(64, ARADIR(1, JB+1), ARADIR(1, JB))
           CALL MOVW(4,NCALB(1,JB+1),NCALB(1,JB))
           CALL MOVW(NUMAREAOPTIONS,OPTION(1,JB+1),OPTION(1,JB))
           FLIP(JB) = FLIP(JB+1)
C --- REST WRACK
           IAR(JB)=IAR(JB+1)
           NTR(JB)=NTR(JB+1)
           IMOD(JB)=IMOD(JB+1)
           CALL MOVW(4767,JBUF(1,JB+1),JBUF(1,JB))
30       CONTINUE
      ENDIF

      NAREA=NAREA-1

      RETURN
      END

C---------------------------------------------------------------------
C       CLOSA() - stub for backwards compatibility
C
C       Programs must change to use the correct name: CLSARA()
C---------------------------------------------------------------------

      SUBROUTINE CLOSA(AREA)
      IMPLICIT NONE
      INTEGER AREA

      CALL CLSARA(AREA)
      RETURN
      END

C---------------------------------------------------------------------
C       CLOSAO() - stub for backwards compatibility
C
C       Programs must change to use the correct name: CLSARA()
C---------------------------------------------------------------------

      SUBROUTINE CLOSAO(AREA)
      IMPLICIT NONE
      INTEGER AREA

      CALL CLSARA(AREA)
      RETURN
      END
